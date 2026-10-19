"""`report_document_renames` — read-only data for the auto-namer review.

The app's DocumentAutoNamer names inbound pool faxes before upload, and the
monthly review measures it by what people do with those names: keep them, or
rename them. Every rename, from either screen, writes a `ProblemActivity` row
`Renamed document: <old> -> <new>` (`mobile_delete_document`'s PATCH and
`mobile_unassigned_document_assign`). Renames of documents with no problem
links — every rename made at assign, since a pool document has no links yet —
are written with `problem=None` and never reach a Mac, so the review has to
read production. This command is that read.

Output is one JSON object per line on stdout (a Cloud Run job's stdout lands
in Cloud Logging as `jsonPayload`):

  * `kind: "rename"` — one per rename. `_emit_document_audit` writes one row
    per linked problem, so rows with the same author and text written within
    two seconds are one rename. `patient_id` is known only for linked rows.
  * `kind: "document"` — one per document created in the window: the name it
    arrived under (`original_file_name`, recorded since emr 0191), the name it
    was first given, its current name, and the renames traced to it.
    `auto_named` is true when the first name differs from the arrival name —
    the auto-namer is the only thing that names a document before upload.
  * `kind: "summary"` — the counts, last.

**Tracing renames to documents is a heuristic, and says so.** A rename row
carries no document id. A document's renames are found by walking back from
its current name: the latest rename after the document was created whose new
name is that name, on the same patient or unlinked, then the same from that
rename's old name. When one rename is claimed by two documents (two faxes both
renamed to "CBC" the same week, unlinked), both are reported
`match: "ambiguous"` and counted apart, never guessed. Documents created up to
`--lookback-days` before the window also take part in claiming, so a rename of
an older document is less likely to be pinned on a new one; they are not
reported.

Nothing is written. On MySQL the session is set READ ONLY for the duration of
the command and restored afterwards. Plain SELECTs under autocommit take no
locks on InnoDB.

The output carries document names, which are clinical text; it carries no
patient names (ids only). Safe to run against prod.
"""
import json
import os
from datetime import datetime, time, timedelta, timezone as dt_tz

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from emr.models import Document, ProblemActivity

RENAME_PREFIX = 'Renamed document: '
ARROW = ' -> '
# One request writes one row per linked problem, in a loop.
FAN_OUT_WINDOW = timedelta(seconds=2)
# `created_on` on the document and on its audit rows come from separate
# `now()` calls in one request; a rename can never precede its document by
# more than this.
CREATION_SLACK = timedelta(seconds=2)


def _parse_day(value, name):
    try:
        day = datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise CommandError(f'--{name} must be YYYY-MM-DD, got {value!r}')
    return datetime.combine(day, time.min, tzinfo=dt_tz.utc)


def _iso(value):
    return value.astimezone(dt_tz.utc).isoformat().replace('+00:00', 'Z') if value else None


def _split_rename(text):
    """(old, new) from the row text, splitting at the FIRST arrow. None when
    the text has no arrow. Tracing does not rely on this split — see
    `_old_name_if_renamed_to`."""
    body = text[len(RENAME_PREFIX):]
    if ARROW not in body:
        return None, None
    old, new = body.split(ARROW, 1)
    return old, new


def _old_name_if_renamed_to(text, name):
    """The old name of a rename row whose NEW name is exactly `name`, else
    None. Matching on the suffix keeps a name that itself contains " -> "
    traceable."""
    suffix = ARROW + name
    if not text.endswith(suffix):
        return None
    return text[len(RENAME_PREFIX):-len(suffix)]


class Rename:
    __slots__ = ('index', 'at', 'author_id', 'author', 'text', 'problem_ids', 'patient_ids', 'claims')

    def __init__(self, index, at, author_id, author, text):
        self.index = index
        self.at = at
        self.author_id = author_id
        self.author = author
        self.text = text
        self.problem_ids = []
        self.patient_ids = set()
        self.claims = []

    @property
    def patient_id(self):
        return next(iter(self.patient_ids)) if len(self.patient_ids) == 1 else None

    @property
    def unlinked(self):
        return not self.problem_ids

    def could_belong_to(self, patient_id):
        # A linked rename names its patient; an unlinked one could be anyone's.
        return self.unlinked or patient_id in self.patient_ids

    def row(self):
        old, new = _split_rename(self.text)
        return {
            'kind': 'rename',
            'n': self.index,
            'at': _iso(self.at),
            'author_id': self.author_id,
            'author': self.author,
            'old': old,
            'new': new,
            'text': self.text if old is None else None,
            'scope': 'unlinked' if self.unlinked else 'problem',
            'problem_ids': sorted(self.problem_ids),
            'patient_id': self.patient_id,
            'documents': sorted(self.claims),
        }


def collapse_rename_rows(rows):
    """Group raw activity rows into renames. `rows` are
    (created_on, author_id, author_username, activity, problem_id, patient_id)
    in any order."""
    renames = []
    open_by_key = {}
    for created_on, author_id, author, text, problem_id, patient_id in sorted(rows, key=lambda r: r[0]):
        key = (author_id, text)
        current = open_by_key.get(key)
        if current is None or created_on - current.at > FAN_OUT_WINDOW:
            current = Rename(len(renames) + 1, created_on, author_id, author, text)
            renames.append(current)
            open_by_key[key] = current
        if problem_id is not None:
            current.problem_ids.append(problem_id)
            if patient_id is not None:
                current.patient_ids.add(patient_id)
    return renames


def trace_renames(created_on, patient_id, name, renames):
    """The renames that took a document from its first name to `name`,
    oldest first, and its first name. Walks back from the current name,
    taking at each step the latest unused rename to that name that could be
    this document's and happened after it was created."""
    chain = []
    used = set()
    upper = None
    current = name
    while True:
        best = None
        for rename in renames:
            if rename.index in used:
                continue
            if rename.at < created_on - CREATION_SLACK:
                continue
            if upper is not None and rename.at > upper:
                continue
            if not rename.could_belong_to(patient_id):
                continue
            old = _old_name_if_renamed_to(rename.text, current)
            if old is None:
                continue
            if best is None or rename.at > best[0].at:
                best = (rename, old)
        if best is None:
            break
        rename, old = best
        chain.insert(0, rename)
        used.add(rename.index)
        upper = rename.at
        current = old
    return chain, current


class Command(BaseCommand):
    help = 'Read-only: document renames and auto-named documents in a window, as JSON lines.'

    def add_arguments(self, parser):
        parser.add_argument('--since', help='First day, YYYY-MM-DD (UTC). Default: 31 days before --until.')
        parser.add_argument('--until', help='Day after the last, YYYY-MM-DD (UTC). Default: now.')
        parser.add_argument('--lookback-days', type=int, default=30,
                            help='Older documents that may claim a rename (not reported). Default 30.')
        parser.add_argument('--summary-only', action='store_true', help='Print only the summary line.')

    def handle(self, *args, **options):
        until = _parse_day(options['until'], 'until') if options['until'] else datetime.now(dt_tz.utc)
        since = _parse_day(options['since'], 'since') if options['since'] else until - timedelta(days=31)
        if since >= until:
            raise CommandError('--since must be before --until')
        if options['lookback_days'] < 0:
            raise CommandError('--lookback-days must not be negative')

        read_only = connection.vendor == 'mysql'
        if read_only:
            with connection.cursor() as cur:
                cur.execute('SET SESSION TRANSACTION READ ONLY')
        try:
            lines = self.report(since, until, timedelta(days=options['lookback_days']))
        finally:
            if read_only:
                with connection.cursor() as cur:
                    cur.execute('SET SESSION TRANSACTION READ WRITE')

        for line in lines:
            if options['summary_only'] and line['kind'] != 'summary':
                continue
            self.stdout.write(json.dumps(line, ensure_ascii=False))

    def report(self, since, until, lookback):
        rows = list(
            ProblemActivity.objects
            .filter(activity__startswith=RENAME_PREFIX, created_on__gte=since, created_on__lt=until)
            .values_list('created_on', 'author_id', 'author__username', 'activity',
                         'problem_id', 'problem__patient_id')
        )
        renames = collapse_rename_rows(rows)

        documents = list(
            Document.objects
            .filter(created_on__gte=since - lookback, created_on__lt=until)
            .order_by('created_on', 'id')
            .values_list('id', 'created_on', 'author_id', 'author__username', 'patient_id',
                         'team_id', 'original_file_name', 'document_name')
        )

        traced = []
        for doc_id, created_on, author_id, author, patient_id, team_id, arrival, name in documents:
            chain, first_name = trace_renames(created_on, patient_id, name or '', renames)
            for rename in chain:
                rename.claims.append(doc_id)
            traced.append((doc_id, created_on, author_id, author, patient_id, team_id, arrival, name, chain, first_name))

        lines = []
        summary = {
            'kind': 'summary',
            'since': _iso(since),
            'until': _iso(until),
            'renames': len(renames),
            'renames_unlinked': sum(1 for r in renames if r.unlinked),
            'renames_unclaimed': sum(1 for r in renames if not r.claims),
            'documents': 0,
            'documents_with_arrival_name': 0,
            'documents_still_in_pool': 0,
            'auto_named': 0,
            'auto_named_kept': 0,
            'auto_named_renamed': 0,
            'not_auto_named_renamed': 0,
            'ambiguous': 0,
        }
        for doc_id, created_on, author_id, author, patient_id, team_id, arrival, name, chain, first_name in traced:
            if created_on < since:
                continue
            ambiguous = any(len(r.claims) > 1 for r in chain)
            match = 'ambiguous' if ambiguous else ('traced' if chain else 'none')
            arrival_stem = os.path.splitext(arrival)[0] if arrival else None
            auto_named = None if arrival_stem is None else first_name != arrival_stem
            in_pool = patient_id is None and team_id is not None

            summary['documents'] += 1
            summary['documents_with_arrival_name'] += arrival_stem is not None
            summary['documents_still_in_pool'] += in_pool
            if ambiguous:
                summary['ambiguous'] += 1
            elif auto_named:
                summary['auto_named'] += 1
                summary['auto_named_renamed' if chain else 'auto_named_kept'] += 1
            elif auto_named is False and chain:
                summary['not_auto_named_renamed'] += 1

            lines.append({
                'kind': 'document',
                'id': doc_id,
                'created_on': _iso(created_on),
                'uploaded_by_id': author_id,
                'uploaded_by': author,
                'patient_id': patient_id,
                'in_pool': in_pool,
                'arrival_name': arrival,
                'first_name': first_name,
                'name': name,
                'auto_named': auto_named,
                'renamed': bool(chain),
                'renames': [r.index for r in chain],
                'match': match,
            })

        return [r.row() for r in renames] + lines + [summary]
