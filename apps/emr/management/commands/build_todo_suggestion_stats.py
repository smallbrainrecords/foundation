"""Rebuild the table behind suggested todos from the visit history.

    python manage.py build_todo_suggestion_stats            # dry run: report, write nothing
    python manage.py build_todo_suggestion_stats --apply    # replace the table

`emr.todo_suggestions` holds the rule. This command reads every finished
visit, counts how often each physician ordered each todo title on each kind of
problem, and REPLACES `TodoSuggestionStat` with the titles that pass the
evidence floor. Each stored title also gets its usual due date, when the
physician's due dates for it are consistent (`usual_due_months`). It is safe
to run as often as wanted: the table is derived, so a rebuild can only bring
it up to date. Nothing else writes to it.

Nothing schedules this. Run it as a Cloud Run job (the recipe is under
"One-off management commands against prod" in the app repository's CLAUDE.md);
habits move slowly, so weekly is plenty.

On MySQL the table is replaced the way `load_icd10_map` replaces its own: the
new rows are written to a staging table in small autocommitted batches,
checked, and swapped in with one atomic `RENAME TABLE`. Production's database
is a db-f1-micro, where a delete-and-insert in one transaction crawls and
blocks; with the swap a reader sees the old table or the new one, never an
empty one. The table it replaced is kept as `<table>_previous` until the next
rebuild. Other databases use a plain transaction.

A rebuild that would leave the table EMPTY when it now holds rows is refused
unless `--allow-empty` is given: an empty result is far more likely a broken
query than a practice that stopped ordering.
"""
import datetime
import json
import logging

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from emr.models import TodoSuggestionStat
from emr.todo_suggestions import (
    MIN_ORDERS, MIN_PATIENTS, build_rows, collect_units, due_dates_as_ordered, order_visit_starts,
)

_LOGGER = logging.getLogger('smallbrain.todo_suggestions')

INSERT_BATCH = 500
# How long the swap may wait for the table's metadata lock; failing here
# leaves the live table untouched.
SWAP_LOCK_WAIT_SECONDS = 120


class Command(BaseCommand):
    help = 'Rebuild TodoSuggestionStat from the visit history (dry run unless --apply).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Replace the table. Without it the command only reports.')
        parser.add_argument('--physician', type=int, action='append', dest='physicians',
                            help='Limit to this physician user id (repeatable). The table is still '
                                 'replaced whole, so use it for a dry run, not with --apply.')
        parser.add_argument('--min-orders', type=int, default=MIN_ORDERS)
        parser.add_argument('--min-patients', type=int, default=MIN_PATIENTS)
        parser.add_argument('--allow-empty', action='store_true',
                            help='Allow a rebuild that leaves the table empty.')

    def say(self, message):
        self.stdout.write(message)
        self.stdout.flush()

    def handle(self, *args, **options):
        apply = options['apply']
        physicians = options['physicians']
        if apply and physicians:
            raise CommandError(
                '--physician with --apply would replace the whole table with those '
                'physicians only. Use --physician for a dry run.'
            )

        self.say('=== Build todo suggestion statistics ===')
        self.say(f"mode            : {'APPLY' if apply else 'dry-run'}")
        self.say(f"evidence floor  : {options['min_orders']} orders, {options['min_patients']} patients")

        units = collect_units(physicians)
        due_dates = due_dates_as_ordered(order_visit_starts(units))
        rows, totals = build_rows(units, options['min_orders'], options['min_patients'], due_dates)
        self.say(f"physicians      : {totals['physicians']}")
        self.say(f"visits          : {totals['visits']}")
        self.say(f"problem opens   : {totals['units']}  ({totals['units_with_an_order']} with an order)")
        self.say(f"orders          : {totals['orders']}  ({totals['distinct_pairs']} distinct title-on-problem pairs)")
        self.say(f"rows to store   : {totals['rows']}")
        # The stored titles all cleared the several-patients floor, so the
        # most common few are safe to print as a sanity check.
        for row in sorted(rows, key=lambda r: -r.n_orders)[:5]:
            self.say(f'                  {row.n_orders:>5} of {row.n_opens:<5} {row.problem_key}  "{row.title}"'
                     + (f'  due {row.usual_due_months} mo' if row.usual_due_months is not None else ''))
        self.say(f"due as ordered  : known for {totals['orders_due_known']} of {totals['orders']} orders, "
                 f"{totals['orders_dated']} of them dated")
        self.say(f"usual due date  : {totals['rows_with_a_due_date']} rows")
        for row in sorted((r for r in rows if r.usual_due_months is not None), key=lambda r: -r.n_orders)[:10]:
            self.say(f'                  {row.n_orders:>5} orders  {row.usual_due_months:>3} mo  '
                     f'{row.problem_key}  "{row.title}"')

        if not apply:
            self.say('Dry run — nothing written. Re-run with --apply to replace the table.')
            return

        before = TodoSuggestionStat.objects.count()
        if not rows and before and not options['allow_empty']:
            raise CommandError(
                f'the rebuild found nothing to store but the table holds {before} rows. '
                'Refusing to empty it; pass --allow-empty if that is really intended.'
            )

        built_on = timezone.now()
        if connection.vendor == 'mysql':
            method = self.replace_by_swap(rows, built_on)
        else:
            method = self.replace_in_transaction(rows, built_on)

        _LOGGER.info(json.dumps({
            'event': 'todo_suggestion_stats_rebuilt',
            'method': method,
            'rows_before': before,
            'rows_after': len(rows),
            **totals,
        }))
        self.say(self.style.SUCCESS(f'Replaced: {before} rows -> {len(rows)} rows.'))

    # ------------------------------------------------------------ MySQL

    def replace_by_swap(self, rows, built_on):
        """Build the new table beside the live one, then rename it into place."""
        quote = connection.ops.quote_name
        live = TodoSuggestionStat._meta.db_table
        staging, previous = live + '_new', live + '_previous'
        # The connection stores UTC; a raw cursor does no conversion of its own.
        stamp = built_on.astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

        with connection.cursor() as cursor:
            # A staging table left by a run that died is rebuilt from scratch.
            cursor.execute(f'DROP TABLE IF EXISTS {quote(staging)}')
            cursor.execute(f'CREATE TABLE {quote(staging)} LIKE {quote(live)}')

            insert = (
                f'INSERT INTO {quote(staging)} '
                '(physician_user_id, problem_key, title_key, title, n_orders, n_opens, n_patients, '
                'usual_due_months, built_on) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
            )
            for start in range(0, len(rows), INSERT_BATCH):
                cursor.executemany(insert, [
                    (row.physician_id, row.problem_key, row.title_key, row.title,
                     row.n_orders, row.n_opens, row.n_patients, row.usual_due_months, stamp)
                    for row in rows[start:start + INSERT_BATCH]
                ])

            cursor.execute(f'SELECT COUNT(*), COALESCE(SUM(n_orders), 0) FROM {quote(staging)}')
            staged = tuple(int(value) for value in cursor.fetchone())
            expected = (len(rows), sum(row.n_orders for row in rows))
            if staged != expected:
                cursor.execute(f'DROP TABLE IF EXISTS {quote(staging)}')
                raise CommandError(
                    f'the staging table does not match what was built ({staged} != {expected}); '
                    'it was dropped and the live table was not touched'
                )

            # The previous rebuild's safety copy goes; this run's takes its name.
            cursor.execute(f'DROP TABLE IF EXISTS {quote(previous)}')
            cursor.execute(f'SET SESSION lock_wait_timeout = {SWAP_LOCK_WAIT_SECONDS}')
            try:
                cursor.execute(
                    f'RENAME TABLE {quote(live)} TO {quote(previous)}, {quote(staging)} TO {quote(live)}'
                )
            except Exception as exc:
                raise CommandError(
                    f'the new table is built in {staging} but could not be swapped in ({exc}). '
                    'The live table is unchanged. Re-run this command.'
                )
        self.say(f'swapped         : the table it replaced is kept as {previous}')
        return 'swap'

    # ------------------------------------------------------------ others

    def replace_in_transaction(self, rows, built_on):
        with transaction.atomic():
            TodoSuggestionStat.objects.all().delete()
            TodoSuggestionStat.objects.bulk_create([
                TodoSuggestionStat(
                    physician_user_id=row.physician_id, problem_key=row.problem_key,
                    title_key=row.title_key, title=row.title, n_orders=row.n_orders,
                    n_opens=row.n_opens, n_patients=row.n_patients,
                    usual_due_months=row.usual_due_months, built_on=built_on,
                )
                for row in rows
            ], batch_size=INSERT_BATCH)
        return 'transaction'
