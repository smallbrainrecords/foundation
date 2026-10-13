"""Backfill ToDo.accomplished_at from each todo's own activity log.

    python manage.py backfill_todo_accomplished_at                  # dry run: counts only
    python manage.py backfill_todo_accomplished_at --apply          # write
    python manage.py backfill_todo_accomplished_at --apply --limit 200   # canary slice
    python manage.py backfill_todo_accomplished_at --rollback       # put back what --apply replaced

Background (2026-10-11). `ToDo.accomplished_at` is what the Macs show — and
what ⌃O dates a completed order by — and for almost every todo completed before
2026-06-11 it is wrong or missing:

  * Migration 0177 (2026-06-14) added the column and backfilled it with
    `created_on`, "the best-available approximation". On the 2026-07-22 copy
    69,828 accomplished todos therefore carry their CREATION time as their
    completion time.
  * Todos created before 2017-03-14 have no `created_on` at all, so the same
    backfill left 11,379 of them with no `accomplished_at`.
  * The legacy web's `update_todo_status` saved with
    `update_fields=["accomplished"]`, so the stamp `ToDo.save()` computes was
    never written. Every completion made through it — 74,011 events from
    2017-03-14 to 2026-06-11 — left no stamp.

What it did leave is the activity log: each of those completions wrote a
TodoActivity row ("Updated status of this todo to <b>accomplished</b>.") at the
moment it happened. That row IS the completion time. This command copies the
latest one onto the todo.

Which todos, exactly. Accomplished todos whose `accomplished_at` is NULL or
equals `created_on` — the two shapes migration 0177 produced. A real stamp is
never touched. For each, the latest completion event is used when:

  * one exists (8,692 legacy todos have none and stay undated — there is
    nothing true to write); and
  * no "not accomplished" event is later than it. The todo is accomplished now,
    so a later un-completion means it was completed again by a path that wrote
    no row, and the event time would be too early (4 todos on the copy); and
  * it is later than what is stored. Never moves a date earlier.

The UPDATE re-checks the same shape per row, so a todo someone changed since
the plan was made is left alone.

It is a bulk UPDATE, so `ToDo.save()` is not involved and no new stamp is
computed; like the other data heals it writes no activity row. It does touch
each affected patient's PatientMutationStamp so a Mac with that chart open
pulls the corrected dates within one poll.

Undo record. Before each batch the old and new values go to the table
`emr_todo_accomplished_at_backfill` (todo_id, old, new, applied_at; first write
wins, so a re-run keeps the ORIGINAL value). `--rollback` restores `old` only
where the todo still holds the `new` value this command wrote, so a completion
made since is never overwritten. The table is left in place; drop it by hand
once the change has been accepted.

Production's database is a db-f1-micro (see CLAUDE.md): rows are written in
batches of 500, one short transaction each — never one large statement. Run it
as a Cloud Run job with a generous task timeout. Idempotent: a corrected row no
longer matches the shape, so a re-run after a crash resumes where it stopped.
"""
import json
import logging
import time
from collections import Counter, namedtuple
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.db.models import Case, F, Max, Q, When
from django.utils import timezone

from emr.models import ToDo, TodoActivity
from emr.mutation_stamp import touch_patient_stamp

_LOGGER = logging.getLogger('smallbrain.todo_accomplished_backfill')

# The only sentences a completion flip has ever been logged as (2026-07-22
# copy: 74,011 + 798 completions, 470 + 8 un-completions; no other row mentions
# a status change). The first pair is written by the legacy web
# (`todo_app.views.update_todo_status`, 2017-03-14 .. 2026-06-11), the second by
# `mobile_update_todo` (from 2026-06-11) — `MobileTodoActivityLogTests` asserts
# that the mobile text is in this tuple, so a reworded row fails a test instead
# of silently making this command find nothing.
DONE_ACTIVITIES = (
    'Updated status of this todo to <b>accomplished</b>.',
    'Updated status to accomplished',
)
UNDONE_ACTIVITIES = (
    'Updated status of this todo to <b>not accomplished</b>.',
    'Updated status to not accomplished',
)

BACKUP_TABLE = 'emr_todo_accomplished_at_backfill'
BATCH_SIZE = 500
# Seconds between batches. The database is a db-f1-micro shared with the live
# service; the pause is what keeps a 72,000-row pass from competing with the
# clinic's own requests (144 batches: about half a minute in total).
DEFAULT_PAUSE = 0.2

Write = namedtuple('Write', 'todo_id patient_id old new')


def build_plan():
    """-> (writes, skipped, seen): what to write, why the rest is left alone,
    and how many candidates there were by shape. Reads only."""
    events = (
        TodoActivity.objects
        .filter(activity__in=DONE_ACTIVITIES + UNDONE_ACTIVITIES)
        .order_by()
        .values_list('todo_id')
        .annotate(
            done=Max(Case(When(activity__in=DONE_ACTIVITIES, then=F('created_on')))),
            undone=Max(Case(When(activity__in=UNDONE_ACTIVITIES, then=F('created_on')))),
        )
    )
    done_at, undone_at = {}, {}
    for todo_id, done, undone in events:
        if done is not None:
            done_at[todo_id] = done
        if undone is not None:
            undone_at[todo_id] = undone

    candidates = (
        ToDo.objects
        .filter(accomplished=True)
        .filter(Q(accomplished_at__isnull=True) | Q(accomplished_at=F('created_on')))
        .order_by('id')
        .values_list('id', 'patient_id', 'accomplished_at')
    )

    writes, skipped, seen = [], Counter(), Counter()
    for todo_id, patient_id, old in candidates.iterator(chunk_size=2000):
        seen['no stamp' if old is None else 'stamp equals created_on'] += 1
        new = done_at.get(todo_id)
        if new is None:
            skipped['no completion event'] += 1
            continue
        undone = undone_at.get(todo_id)
        if undone is not None and undone > new:
            skipped['un-completed after its last completion event'] += 1
            continue
        if old is not None and new <= old:
            skipped['event not later than the stored stamp'] += 1
            continue
        writes.append(Write(todo_id, patient_id, old, new))
    return writes, skipped, seen


def _ensure_backup_table():
    quoted = connection.ops.quote_name(BACKUP_TABLE)
    with connection.cursor() as cursor:
        # DDL commits implicitly on MySQL, so this is deliberately outside any
        # transaction.atomic block.
        cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {quoted} ('
            'todo_id BIGINT NOT NULL PRIMARY KEY, '
            'old_accomplished_at DATETIME(6) NULL, '
            'new_accomplished_at DATETIME(6) NOT NULL, '
            'applied_at DATETIME(6) NOT NULL'
            ') ENGINE=InnoDB'
        )


def apply_writes(writes, progress=None, pause=0.0):
    """Write `writes` in short transactions; -> (rows_written, patient_ids).

    The UPDATE carries the candidate shape in its WHERE clause, so a todo that
    changed after the plan was built matches nothing and is left alone.
    """
    _ensure_backup_table()
    backup = connection.ops.quote_name(BACKUP_TABLE)
    todo = connection.ops.quote_name(ToDo._meta.db_table)
    adapt = connection.ops.adapt_datetimefield_value
    applied_at = adapt(timezone.now())

    written, patients = 0, set()
    for start in range(0, len(writes), BATCH_SIZE):
        batch = writes[start:start + BATCH_SIZE]
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.executemany(
                f'INSERT IGNORE INTO {backup} '
                '(todo_id, old_accomplished_at, new_accomplished_at, applied_at) VALUES (%s, %s, %s, %s)',
                [(w.todo_id, adapt(w.old) if w.old is not None else None, adapt(w.new), applied_at)
                 for w in batch],
            )
            for w in batch:
                cursor.execute(
                    f'UPDATE {todo} SET accomplished_at = %s '
                    'WHERE id = %s AND accomplished = 1 '
                    'AND (accomplished_at IS NULL OR accomplished_at = created_on)',
                    [adapt(w.new), w.todo_id],
                )
                if cursor.rowcount:
                    written += 1
                    if w.patient_id:
                        patients.add(w.patient_id)
        if progress:
            progress(written, len(writes))
        if pause:
            time.sleep(pause)
    return written, patients


def rollback_writes(progress=None, pause=0.0):
    """Restore `old` wherever the todo still holds the value this command
    wrote. -> (rows_restored, patient_ids). Raises CommandError if there is
    nothing to roll back."""
    if BACKUP_TABLE not in connection.introspection.table_names():
        raise CommandError(f'Nothing to roll back: table {BACKUP_TABLE} does not exist.')
    backup = connection.ops.quote_name(BACKUP_TABLE)
    todo = connection.ops.quote_name(ToDo._meta.db_table)
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT todo_id FROM {backup} ORDER BY todo_id')
        ids = [row[0] for row in cursor.fetchall()]

    restored, patients = 0, set()
    for start in range(0, len(ids), BATCH_SIZE):
        chunk = ids[start:start + BATCH_SIZE]
        marks = ', '.join(['%s'] * len(chunk))
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                f'SELECT t.id, t.patient_id FROM {todo} t JOIN {backup} b ON b.todo_id = t.id '
                f'WHERE b.todo_id IN ({marks}) AND t.accomplished_at = b.new_accomplished_at',
                chunk,
            )
            touched = cursor.fetchall()
            cursor.execute(
                f'UPDATE {todo} t JOIN {backup} b ON b.todo_id = t.id '
                'SET t.accomplished_at = b.old_accomplished_at '
                f'WHERE b.todo_id IN ({marks}) AND t.accomplished_at = b.new_accomplished_at',
                chunk,
            )
            restored += cursor.rowcount
        patients.update(patient_id for _, patient_id in touched if patient_id)
        if progress:
            progress(restored, len(ids))
        if pause:
            time.sleep(pause)
    return restored, patients


def _touch_stamps(patient_ids):
    """Best-effort, like every other caller: a stamp failure never fails a
    completed data heal."""
    stamped = 0
    for patient_id in patient_ids:
        try:
            touch_patient_stamp(patient_id)
            stamped += 1
        except Exception:
            pass
    return stamped


class Command(BaseCommand):
    help = 'Backfill ToDo.accomplished_at from the todo activity log (dry run unless --apply).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Write the corrected completion times. Without it, report only.')
        parser.add_argument('--limit', type=int, default=None, metavar='N',
                            help='With --apply: write only the first N todos by id (a canary slice).')
        parser.add_argument('--rollback', action='store_true',
                            help=f'Restore the values --apply replaced, from {BACKUP_TABLE}.')
        parser.add_argument('--pause', type=float, default=DEFAULT_PAUSE, metavar='SECONDS',
                            help=f'Sleep between batches (default {DEFAULT_PAUSE}).')

    def handle(self, *args, **options):
        if options['rollback']:
            if options['apply']:
                raise CommandError('--rollback and --apply are exclusive.')
            return self._rollback(options['pause'])
        return self._plan_and_maybe_apply(options['apply'], options['limit'], options['pause'])

    # -- rollback --------------------------------------------------------

    def _rollback(self, pause):
        self.stdout.write('=== ToDo.accomplished_at backfill: ROLLBACK ===')
        started = time.monotonic()
        restored, patients = rollback_writes(self._progress(started), pause)
        stamped = _touch_stamps(patients)
        self.stdout.write(f'rows restored           : {restored}')
        self.stdout.write(f'patients affected       : {len(patients)}')
        self.stdout.write(f'mutation stamps touched : {stamped}')
        _LOGGER.info(json.dumps({'event': 'todo_accomplished_backfill_rollback', 'restored': restored}))

    # -- plan / apply ----------------------------------------------------

    def _plan_and_maybe_apply(self, apply, limit, pause):
        started = time.monotonic()
        now = timezone.now()
        cutoff = now - timedelta(days=365)

        writes, skipped, seen = build_plan()
        total_accomplished = ToDo.objects.filter(accomplished=True).count()
        in_window_now = ToDo.objects.filter(accomplished=True, accomplished_at__gte=cutoff).count()
        # A write only ever moves a date later, so nothing can leave the window.
        enters = sum(1 for w in writes if w.new >= cutoff and not (w.old is not None and w.old >= cutoff))

        fills = sum(1 for w in writes if w.old is None)
        corrects = len(writes) - fills
        by_year = Counter(w.new.year for w in writes)

        self.stdout.write('=== ToDo.accomplished_at backfill ===')
        self.stdout.write(f"mode                          : {'APPLY' if apply else 'dry-run'}")
        self.stdout.write(f'accomplished todos            : {total_accomplished}')
        self.stdout.write(f"  candidates, no stamp        : {seen['no stamp']}")
        self.stdout.write(f"  candidates, stamp==created  : {seen['stamp equals created_on']}")
        self.stdout.write(f'will fill (NULL -> event)     : {fills}')
        self.stdout.write(f'will correct (created -> event): {corrects}')
        for reason, n in sorted(skipped.items()):
            self.stdout.write(f'left alone: {reason:<44}: {n}')
        self.stdout.write(
            f'completions dated inside the last 12 months: {in_window_now} -> '
            f'{in_window_now + enters}  (+{enters})')
        self.stdout.write('new completion dates by year   : '
                          + ', '.join(f'{y}: {n}' for y, n in sorted(by_year.items())))
        for w in writes[:5]:
            self.stdout.write(f'  sample todo {w.todo_id}: {w.old} -> {w.new}')

        if not apply:
            self.stdout.write('Dry run — nothing written. Use --apply (optionally --limit N first).')
            return

        if limit is not None:
            writes = writes[:max(0, limit)]
            self.stdout.write(f'--limit {limit}: writing the first {len(writes)} only.')

        written, patients = apply_writes(writes, self._progress(started), pause)
        stamped = _touch_stamps(patients)
        self.stdout.write('')
        self.stdout.write(f'rows written            : {written}')
        self.stdout.write(f'changed since the plan  : {len(writes) - written} (left alone)')
        self.stdout.write(f'patients affected       : {len(patients)}')
        self.stdout.write(f'mutation stamps touched : {stamped}')
        self.stdout.write(f'undo record             : {BACKUP_TABLE} (--rollback restores it)')
        self.stdout.write(f'elapsed                 : {time.monotonic() - started:.1f}s')
        _LOGGER.info(json.dumps({
            'event': 'todo_accomplished_backfill',
            'written': written,
            'planned': len(writes),
            'patients': len(patients),
        }))

    def _progress(self, started):
        def report(done, total):
            self.stdout.write(f'  ...{done}/{total} ({time.monotonic() - started:.0f}s)')
        return report
