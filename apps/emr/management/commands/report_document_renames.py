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
  * `kind: "document"` — one per document created in the window: where it
    was uploaded (`origin`), the name it arrived under (`original_file_name`,
    recorded since emr 0191), the name it was first given, its current name,
    and the renames traced to it.
  * `kind: "summary"` — the counts, last.

**Origin: pool or chart.** A chart upload (`mobile_upload_document`) writes
`Added document: <name>` by the uploader in the same request; a pool upload
writes nothing until it is assigned, later and usually by someone else. So a
document with an `Added document:` row by its uploader within two seconds of
its creation came from a chart, and its first name is that row's name. Only
pool uploads are named by the auto-namer, so `auto_named` is true only for a
pool document whose first name differs from its arrival name. A chart
document whose first name differs (`named_before_upload`) was named by a
person before its upload landed; the window measured on 2026-10-20 had none.

**Tracing renames to documents is a heuristic, and says so.** A rename row
carries no document id. Three things narrow it:
  1. A rename whose old name is exactly one candidate document's arrival name,
     or a chart upload's creation name, is that document's (`anchored`) —
     those names are scanner stamps and fax file names, nearly unique.
  2. A document still in the pool has never been renamed (pool documents have
     no rename endpoint; the name changes at assign).
  3. A chart document's renames must lead back to its creation name.
Beyond that, a document's renames are found by walking back from its current
name: the latest unclaimed rename after the document was created whose new
name is that name, on the same patient or unlinked. When one unanchored rename
is claimed by two documents, both are reported `match: "ambiguous"` and
counted apart, never guessed. Documents created up to `--lookback-days` before
the window also take part in claiming and anchoring; they are not reported.
The default is 120 days because a document is often renamed months after it
arrived: on the 2026-10-20 run the largest ambiguous groups were renames of
documents uploaded in June and July (19 documents claimed one rename of a
July document). A wider lookback can only anchor more renames or reveal a
claim that was a guess.

Nothing is written. On MySQL the session is set READ ONLY for the duration of
the command and restored afterwards. Plain SELECTs under autocommit take no
locks on InnoDB.

The output carries document names, which are clinical text; it carries no
patient names (ids only). Safe to run against prod.
"""
import json
import os
from collections import defaultdict
from datetime import datetime, time, timedelta, timezone as dt_tz

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.models import Q

from emr.models import Document, ProblemActivity

RENAME_PREFIX = 'Renamed document: '
ADDED_PREFIX = 'Added document: '
ARROW = ' -> '
# One request writes one row per linked problem, in a loop.
FAN_OUT_WINDOW = timedelta(seconds=2)
# `created_on` on the document and on its audit rows come from separate
# `now()` calls in one request.
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
    __slots__ = ('index', 'at', 'author_id', 'author', 'text', 'problem_ids', 'patient_ids',
                 'anchor', 'claims')

    def __init__(self, index, at, author_id, author, text):
        self.index = index
        self.at = at
        self.author_id = author_id
        self.author = author
        self.text = text
        self.problem_ids = []
        self.patient_ids = set()
        self.anchor = None
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
            'anchored': self.anchor is not None,
            'documents': sorted(self.claims),
        }


class Doc:
    __slots__ = ('id', 'created_on', 'author_id', 'author', 'patient_id', 'team_id', 'arrival',
                 'name', 'creation_names', 'creation_name', 'chain', 'first_name', 'consistent')

    def __init__(self, doc_id, created_on, author_id, author, patient_id, team_id, arrival, name):
        self.id = doc_id
        self.created_on = created_on
        self.author_id = author_id
        self.author = author
        self.patient_id = patient_id
        self.team_id = team_id
        self.arrival = arrival
        self.name = name or ''
        self.creation_names = set()
        self.creation_name = None
        self.chain = []
        self.first_name = self.name
        self.consistent = True

    @property
    def in_pool(self):
        return self.patient_id is None and self.team_id is not None

    @property
    def origin(self):
        return 'chart' if self.creation_names else 'pool'

    @property
    def arrival_stem(self):
        return os.path.splitext(self.arrival)[0] if self.arrival else None

    def could_own(self, rename):
        if self.in_pool:
            return False   # never renamed: the pool has no rename endpoint
        if rename.at < self.created_on - CREATION_SLACK:
            return False
        return rename.could_belong_to(self.patient_id)


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


def mark_chart_uploads(docs, added_rows):
    """A chart upload writes `Added document: <name>` by the uploader in the
    same request. `added_rows` are (created_on, author_id, activity).

    `creation_names` holds every such row near the document's creation, which
    is enough to call it a chart upload. When one person uploads several
    documents within the same two seconds — a stranded batch retried at once
    — every document in the batch sees every row, so the document's OWN name
    is resolved separately (`creation_name`): the row naming its arrival
    name, else the only row, else the row naming its current name. Measured:
    anchoring on the whole set unanchored all 25 "phq" renames on the
    2026-10-20 run, because their scans were uploaded in batches."""
    by_author = defaultdict(list)
    for at, author_id, text in added_rows:
        by_author[author_id].append((at, text[len(ADDED_PREFIX):]))
    for doc in docs:
        doc.creation_names = {
            name for at, name in by_author.get(doc.author_id, ())
            if abs(at - doc.created_on) <= CREATION_SLACK
        }
        if doc.arrival_stem in doc.creation_names:
            doc.creation_name = doc.arrival_stem
        elif len(doc.creation_names) == 1:
            doc.creation_name = next(iter(doc.creation_names))
        elif doc.name in doc.creation_names:
            doc.creation_name = doc.name


def anchor_renames(docs, renames):
    """A rename whose old name is exactly one candidate document's arrival
    name or chart creation name belongs to that document. Run after
    `mark_chart_uploads`."""
    by_name = defaultdict(set)
    for doc in docs:
        if doc.arrival_stem:
            by_name[doc.arrival_stem].add(doc)
        if doc.creation_name:
            by_name[doc.creation_name].add(doc)
    for rename in renames:
        old, _ = _split_rename(rename.text)
        owners = [doc for doc in by_name.get(old, ()) if doc.could_own(rename)]
        if len(owners) == 1:
            rename.anchor = owners[0].id


def trace_renames(doc, renames):
    """Set `doc.chain` (oldest first) and `doc.first_name`. Walks back from
    the current name, taking at each step the latest rename to that name that
    this document could own and no other document is anchored to; then keeps
    the longest stretch of that walk that ends where the document must have
    started — its creation name for a chart upload, its arrival name for a
    pool upload when the walk reaches it."""
    if doc.in_pool:
        return
    walk = [([], doc.name)]
    used = set()
    upper = None
    current = doc.name
    while True:
        best = None
        for rename in renames:
            if rename.index in used or not doc.could_own(rename):
                continue
            if rename.anchor is not None and rename.anchor != doc.id:
                continue
            if upper is not None and rename.at > upper:
                continue
            old = _old_name_if_renamed_to(rename.text, current)
            if old is None:
                continue
            if best is None or rename.at > best[0].at:
                best = (rename, old)
        if best is None:
            break
        rename, old = best
        used.add(rename.index)
        upper = rename.at
        current = old
        walk.append(([rename] + walk[-1][0], current))

    if doc.creation_names:
        own = {doc.creation_name} if doc.creation_name else doc.creation_names
        starts = [step for step in walk if step[1] in own]
        doc.consistent = bool(starts)
        chosen = starts[-1] if starts else walk[-1]
    elif doc.arrival_stem is not None and any(step[1] == doc.arrival_stem for step in walk):
        chosen = [step for step in walk if step[1] == doc.arrival_stem][-1]
    else:
        chosen = walk[-1]
    doc.chain, doc.first_name = chosen


class Command(BaseCommand):
    help = 'Read-only: document renames and auto-named documents in a window, as JSON lines.'

    def add_arguments(self, parser):
        parser.add_argument('--since', help='First day, YYYY-MM-DD (UTC). Default: 31 days before --until.')
        parser.add_argument('--until', help='Day after the last, YYYY-MM-DD (UTC). Default: now.')
        parser.add_argument('--lookback-days', type=int, default=120,
                            help='Older documents that may own a rename (not reported). Default 120.')
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
        earliest = since - lookback - CREATION_SLACK
        # One pass over the activity table for both kinds of row.
        activity = list(
            ProblemActivity.objects
            .filter(Q(activity__startswith=RENAME_PREFIX) | Q(activity__startswith=ADDED_PREFIX),
                    created_on__gte=earliest, created_on__lt=until)
            .values_list('created_on', 'author_id', 'author__username', 'activity',
                         'problem_id', 'problem__patient_id')
        )
        renames = collapse_rename_rows([
            row for row in activity
            if row[3].startswith(RENAME_PREFIX) and row[0] >= since
        ])
        added_rows = [(row[0], row[1], row[3]) for row in activity if row[3].startswith(ADDED_PREFIX)]

        docs = [
            Doc(*values) for values in
            Document.objects
            .filter(created_on__gte=since - lookback, created_on__lt=until)
            .order_by('created_on', 'id')
            .values_list('id', 'created_on', 'author_id', 'author__username', 'patient_id',
                         'team_id', 'original_file_name', 'document_name')
        ]
        mark_chart_uploads(docs, added_rows)
        anchor_renames(docs, renames)
        for doc in docs:
            trace_renames(doc, renames)
            for rename in doc.chain:
                rename.claims.append(doc.id)

        summary = {
            'kind': 'summary',
            'since': _iso(since),
            'until': _iso(until),
            'renames': len(renames),
            'renames_unlinked': sum(1 for r in renames if r.unlinked),
            'renames_anchored': sum(1 for r in renames if r.anchor is not None),
            'renames_unclaimed': sum(1 for r in renames if not r.claims),
            'documents': 0,
            'from_pool': 0,
            'from_chart': 0,
            'still_in_pool': 0,
            'with_arrival_name': 0,
            'auto_named': 0,
            'auto_named_kept': 0,
            'auto_named_renamed': 0,
            'auto_named_still_in_pool': 0,
            'pool_not_auto_named': 0,
            'pool_not_auto_named_renamed': 0,
            'chart_named_before_upload': 0,
            'ambiguous': 0,
            'inconsistent': 0,
        }
        lines = []
        for doc in docs:
            if doc.created_on < since:
                continue
            ambiguous = any(len(r.claims) > 1 for r in doc.chain)
            if ambiguous:
                match = 'ambiguous'
            elif not doc.consistent:
                match = 'inconsistent'
            else:
                match = 'traced' if doc.chain else 'none'
            stem = doc.arrival_stem
            named_before_upload = None if stem is None else doc.first_name != stem
            auto_named = (named_before_upload if doc.origin == 'pool' else False) if stem is not None else None

            summary['documents'] += 1
            summary['from_' + doc.origin] += 1
            summary['still_in_pool'] += doc.in_pool
            summary['with_arrival_name'] += stem is not None
            if match == 'ambiguous':
                summary['ambiguous'] += 1
            elif match == 'inconsistent':
                summary['inconsistent'] += 1
            elif doc.origin == 'chart':
                summary['chart_named_before_upload'] += bool(named_before_upload)
            elif auto_named:
                summary['auto_named'] += 1
                if doc.in_pool:
                    summary['auto_named_still_in_pool'] += 1
                else:
                    summary['auto_named_renamed' if doc.chain else 'auto_named_kept'] += 1
            elif auto_named is False:
                summary['pool_not_auto_named'] += 1
                summary['pool_not_auto_named_renamed'] += bool(doc.chain)

            lines.append({
                'kind': 'document',
                'id': doc.id,
                'created_on': _iso(doc.created_on),
                'uploaded_by_id': doc.author_id,
                'uploaded_by': doc.author,
                'patient_id': doc.patient_id,
                'origin': doc.origin,
                'in_pool': doc.in_pool,
                'arrival_name': doc.arrival,
                'first_name': doc.first_name,
                'name': doc.name,
                'named_before_upload': named_before_upload,
                'auto_named': auto_named,
                'renamed': bool(doc.chain),
                'renames': [r.index for r in doc.chain],
                'match': match,
            })

        return [r.row() for r in renames] + lines + [summary]
