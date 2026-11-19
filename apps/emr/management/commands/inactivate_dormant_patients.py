"""Make patients who have had no encounter in the past N years inactive.

    python manage.py inactivate_dormant_patients                    # dry run: counts only
    python manage.py inactivate_dormant_patients --apply            # write
    python manage.py inactivate_dormant_patients --apply --limit 20 # canary slice
    python manage.py inactivate_dormant_patients --spare-charted    # keep charts still in use
    python manage.py inactivate_dormant_patients --rollback         # make them active again

Owner request 2026-11-19: "make any patient who has not had an appointment in
the past 7 years inactive", with "encounter is an appointment". Small Brain has
no appointment table; an `emr.Encounter` row is a visit. Encounters go back to
2017-03-14, so a 7-year window is covered by them in full.

What "inactive" means. The account's `User.is_active` flag — the same switch as
the Active toggle in the app's Settings (`mobile_toggle_user_active`). Chart
access does not look at it (`_assert_patient_access`, `_accessible_patient_ids`),
so staff keep full use of the chart. What changes:
  * the patient is listed under "Inactive Patients" in the sidebar search;
  * the home-page search across charts covers active patients only, and the
    background chart-text download skips inactive charts (a chart's own Search
    tab still works);
  * the patient can no longer sign in to the app themselves, and a session
    they hold is ended (Django's ModelBackend refuses inactive users).
`PatientController.is_active` is a different flag and is not touched.

Which patients. Accounts with role 'patient' that are active now and have no
encounter that STARTED within the window. A patient whose account was created
within the window is left alone unless `--include-new` is given: they have not
yet gone N years without a visit (a new patient waiting for a first visit has
no encounter at all). With `--spare-charted`, a patient with a todo or a
document added in the past 12 months is also left alone: someone is still
working that chart (owner decision 2026-11-19, after the production dry run
found 21 such patients among 293, five of them Ryan family charts with no
recorded visit). The UPDATE re-checks every condition per row, so a patient
seen, charted, or switched off by hand after the plan was made is left alone.

Undo record. Before each batch the patient id and their last encounter go to
the table `emr_dormant_patient_inactivation` (user_id, last_encounter,
applied_at; first write wins). `--rollback` makes active again every patient in
it who is still inactive — including one a person switched off by hand since,
which cannot be told apart. Drop the table by hand once the change is accepted.

No PatientMutationStamp is touched: the flag is not chart content. The Macs
read it from the patient list and the search list, which they re-read on their
own schedule.

Production's database is a db-f1-micro (see CLAUDE.md): rows are written in
batches of 200, one short transaction each. Idempotent: a re-run finds nothing
already done.
"""
import json
import logging
import time
from collections import Counter, namedtuple
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone

from emr.models import Document, Encounter, ToDo, UserProfile

_LOGGER = logging.getLogger('smallbrain.dormant_patients')

BACKUP_TABLE = 'emr_dormant_patient_inactivation'
BATCH_SIZE = 200
DEFAULT_PAUSE = 0.2
DEFAULT_YEARS = 7
CHARTED_WINDOW = timedelta(days=365)
SPARED_REASON = 'todo or document added in the past 12 months'

Candidate = namedtuple('Candidate', 'user_id last_encounter date_joined last_login')


def cutoff_for(now, years):
    """`now` moved back `years` calendar years (29 Feb -> 28 Feb)."""
    try:
        return now.replace(year=now.year - years)
    except ValueError:
        return now.replace(year=now.year - years, day=28)


def build_plan(cutoff, include_new=False, charted_since=None):
    """-> (candidates, skipped): who would be made inactive, and why the other
    dormant patients are left alone. With `charted_since`, a patient with a
    todo or document added since then is left alone. Reads only."""
    active_patients = (
        UserProfile.objects
        .filter(role='patient', user__is_active=True)
        .values_list('user_id', 'user__date_joined', 'user__last_login')
    )
    last_visit = dict(
        Encounter.objects.order_by().values_list('patient_id')
        .annotate(last=Max('starttime')).values_list('patient_id', 'last')
    )

    candidates, skipped = [], Counter()
    for user_id, date_joined, last_login in active_patients.iterator(chunk_size=2000):
        last = last_visit.get(user_id)
        if last is not None and last >= cutoff:
            continue
        if not include_new and date_joined is not None and date_joined >= cutoff:
            skipped['account created within the window'] += 1
            continue
        candidates.append(Candidate(user_id, last, date_joined, last_login))
    if charted_since is not None:
        charted = recently_charted((c.user_id for c in candidates), charted_since)
        skipped[SPARED_REASON] += sum(1 for c in candidates if c.user_id in charted)
        candidates = [c for c in candidates if c.user_id not in charted]
    candidates.sort(key=lambda c: c.user_id)
    return candidates, skipped


def recently_charted(user_ids, since):
    """-> the subset of `user_ids` with a todo or a document created since
    `since`. Reported, never used to decide."""
    ids = list(user_ids)
    found = set()
    for start in range(0, len(ids), 1000):
        chunk = ids[start:start + 1000]
        found.update(ToDo.objects.filter(patient_id__in=chunk, created_on__gte=since)
                     .order_by().values_list('patient_id', flat=True).distinct())
        found.update(Document.objects.filter(patient_id__in=chunk, created_on__gte=since)
                     .order_by().values_list('patient_id', flat=True).distinct())
    return found


def _ensure_backup_table():
    quoted = connection.ops.quote_name(BACKUP_TABLE)
    with connection.cursor() as cursor:
        # DDL commits implicitly on MySQL: deliberately outside any atomic block.
        cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {quoted} ('
            'user_id BIGINT NOT NULL PRIMARY KEY, '
            'last_encounter DATETIME(6) NULL, '
            'applied_at DATETIME(6) NOT NULL'
            ') ENGINE=InnoDB'
        )


def apply_inactivation(candidates, cutoff, include_new=False, progress=None, pause=0.0,
                       charted_since=None):
    """Switch `candidates` off in short transactions; -> rows written.

    The UPDATE carries the plan's conditions, so a patient seen (or, with
    `charted_since`, charted) since the plan was made, or already inactive,
    matches nothing and is left alone.
    """
    _ensure_backup_table()
    backup = connection.ops.quote_name(BACKUP_TABLE)
    user = connection.ops.quote_name(User._meta.db_table)
    encounter = connection.ops.quote_name(Encounter._meta.db_table)
    adapt = connection.ops.adapt_datetimefield_value
    applied_at = adapt(timezone.now())
    cut = adapt(cutoff)
    joined_clause = '' if include_new else ' AND date_joined < %s'
    charted_clause, charted_params = '', []
    if charted_since is not None:
        todo = connection.ops.quote_name(ToDo._meta.db_table)
        document = connection.ops.quote_name(Document._meta.db_table)
        charted_clause = (
            f' AND NOT EXISTS (SELECT 1 FROM {todo} t WHERE t.patient_id = {user}.id AND t.created_on >= %s)'
            f' AND NOT EXISTS (SELECT 1 FROM {document} d WHERE d.patient_id = {user}.id AND d.created_on >= %s)'
        )
        charted_params = [adapt(charted_since), adapt(charted_since)]

    written = 0
    for start in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[start:start + BATCH_SIZE]
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.executemany(
                f'INSERT IGNORE INTO {backup} (user_id, last_encounter, applied_at) VALUES (%s, %s, %s)',
                [(c.user_id, adapt(c.last_encounter) if c.last_encounter else None, applied_at)
                 for c in batch],
            )
            for c in batch:
                params = [c.user_id] + ([] if include_new else [cut]) + [cut] + charted_params
                cursor.execute(
                    f'UPDATE {user} SET is_active = 0 '
                    f'WHERE id = %s AND is_active = 1{joined_clause} '
                    f'AND NOT EXISTS (SELECT 1 FROM {encounter} e '
                    f'WHERE e.patient_id = {user}.id AND e.starttime >= %s)'
                    f'{charted_clause}',
                    params,
                )
                written += cursor.rowcount
            # A row planned but left alone is not this command's work: keep the
            # undo record to what it actually switched off.
            marks = ', '.join(['%s'] * len(batch))
            cursor.execute(
                f'DELETE b FROM {backup} b JOIN {user} u ON u.id = b.user_id '
                f'WHERE b.user_id IN ({marks}) AND b.applied_at = %s AND u.is_active = 1',
                [c.user_id for c in batch] + [applied_at],
            )
        if progress:
            progress(written, len(candidates))
        if pause:
            time.sleep(pause)
    return written


def rollback_inactivation(progress=None, pause=0.0):
    """Make active again every patient in the undo record who is still
    inactive. -> rows restored. Raises CommandError if there is no record."""
    if BACKUP_TABLE not in connection.introspection.table_names():
        raise CommandError(f'Nothing to roll back: table {BACKUP_TABLE} does not exist.')
    backup = connection.ops.quote_name(BACKUP_TABLE)
    user = connection.ops.quote_name(User._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT user_id FROM {backup} ORDER BY user_id')
        ids = [row[0] for row in cursor.fetchall()]

    restored = 0
    for start in range(0, len(ids), BATCH_SIZE):
        chunk = ids[start:start + BATCH_SIZE]
        marks = ', '.join(['%s'] * len(chunk))
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE {user} SET is_active = 1 WHERE id IN ({marks}) AND is_active = 0', chunk)
            restored += cursor.rowcount
        if progress:
            progress(restored, len(ids))
        if pause:
            time.sleep(pause)
    return restored


class Command(BaseCommand):
    help = 'Make patients with no encounter in the past N years inactive (dry run unless --apply).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Switch the patients off. Without it, report only.')
        parser.add_argument('--years', type=int, default=DEFAULT_YEARS, metavar='N',
                            help=f'Window in calendar years (default {DEFAULT_YEARS}).')
        parser.add_argument('--include-new', action='store_true',
                            help='Also switch off patients whose account was created within the window.')
        parser.add_argument('--spare-charted', action='store_true',
                            help='Leave alone patients with a todo or document added in the past 12 months.')
        parser.add_argument('--limit', type=int, default=None, metavar='N',
                            help='With --apply: switch off only the first N patients by id (a canary slice).')
        parser.add_argument('--rollback', action='store_true',
                            help=f'Make active again every patient recorded in {BACKUP_TABLE}.')
        parser.add_argument('--pause', type=float, default=DEFAULT_PAUSE, metavar='SECONDS',
                            help=f'Sleep between batches (default {DEFAULT_PAUSE}).')

    def handle(self, *args, **options):
        if options['rollback']:
            if options['apply']:
                raise CommandError('--rollback and --apply are exclusive.')
            return self._rollback(options['pause'])
        if options['years'] < 1:
            raise CommandError('--years must be at least 1.')
        return self._plan_and_maybe_apply(options)

    def _rollback(self, pause):
        self.stdout.write('=== Dormant patients: ROLLBACK ===')
        started = time.monotonic()
        restored = rollback_inactivation(self._progress(started), pause)
        self.stdout.write(f'patients made active again : {restored}')
        _LOGGER.info(json.dumps({'event': 'dormant_patients_rollback', 'restored': restored}))

    def _plan_and_maybe_apply(self, options):
        apply, years, include_new = options['apply'], options['years'], options['include_new']
        started = time.monotonic()
        now = timezone.now()
        cutoff = cutoff_for(now, years)
        charted_since = now - CHARTED_WINDOW if options['spare_charted'] else None

        candidates, skipped = build_plan(cutoff, include_new, charted_since)
        patients = UserProfile.objects.filter(role='patient')
        total = patients.count()
        active = patients.filter(user__is_active=True).count()
        never = sum(1 for c in candidates if c.last_encounter is None)
        by_year = Counter(c.last_encounter.year for c in candidates if c.last_encounter)
        logged_in = sum(1 for c in candidates if c.last_login and c.last_login >= cutoff)
        charted = sorted(recently_charted((c.user_id for c in candidates), now - CHARTED_WINDOW))
        first_visit = Encounter.objects.order_by('starttime').values_list('starttime', flat=True).first()

        self.stdout.write('=== Dormant patients ===')
        self.stdout.write(f"mode                              : {'APPLY' if apply else 'dry-run'}")
        self.stdout.write(f'window                            : no encounter since {cutoff:%Y-%m-%d} ({years} years)')
        self.stdout.write(f'earliest encounter on record      : {first_visit:%Y-%m-%d}' if first_visit
                          else 'earliest encounter on record      : none')
        self.stdout.write(f'patients                          : {total} ({active} active)')
        self.stdout.write(f'will make inactive                : {len(candidates)}')
        self.stdout.write(f'  never had an encounter          : {never}')
        self.stdout.write('  last encounter by year          : '
                          + (', '.join(f'{y}: {n}' for y, n in sorted(by_year.items())) or '-'))
        for reason, n in sorted(skipped.items()):
            self.stdout.write(f'left active: {reason:<35}: {n}')
        self.stdout.write(f'  signed in to the app within the window : {logged_in}')
        self.stdout.write(f'  with a todo or document added in the past 12 months: {len(charted)}')
        if charted:
            self.stdout.write('    patient ids: ' + ', '.join(str(i) for i in charted))
        self.stdout.write(f'active patients after             : {active - len(candidates)}')

        if not apply:
            self.stdout.write('Dry run - nothing written. Use --apply (optionally --limit N first).')
            return

        if options['limit'] is not None:
            candidates = candidates[:max(0, options['limit'])]
            self.stdout.write(f"--limit {options['limit']}: switching off the first {len(candidates)} only.")

        written = apply_inactivation(candidates, cutoff, include_new,
                                     self._progress(started), options['pause'], charted_since)
        self.stdout.write('')
        self.stdout.write(f'patients made inactive  : {written}')
        self.stdout.write(f'changed since the plan  : {len(candidates) - written} (left alone)')
        self.stdout.write(f'undo record             : {BACKUP_TABLE} (--rollback restores it)')
        self.stdout.write(f'elapsed                 : {time.monotonic() - started:.1f}s')
        _LOGGER.info(json.dumps({
            'event': 'dormant_patients_inactivated',
            'written': written,
            'planned': len(candidates),
            'years': years,
            'include_new': include_new,
            'spare_charted': charted_since is not None,
        }))

    def _progress(self, started):
        def report(done, total):
            self.stdout.write(f'  ...{done}/{total} ({time.monotonic() - started:.0f}s)')
        return report
