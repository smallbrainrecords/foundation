"""Measure suggested todos against history. Read-only.

    python manage.py replay_todo_suggestions
    python manage.py replay_todo_suggestions --since 2025-01-01 --physician 16

Every problem opened in a visit on or after `--since` is ranked using only the
visits before it, and the titles really ordered are looked for in that
ranking. This is the acceptance check for the rule in `emr.todo_suggestions`:
on the owner's 2025-26 visits the exact title ordered was the most often
ordered one about 21% of the time, among the top three about 32% and among
the top five about 36%. A result far from those means the rule here no longer
matches what was measured, and the app half should not ship on it.

It also prints what the app would really show at a few cutoffs (at most three
titles that pass the evidence floor), which is the table a cutoff is chosen
from: how many titles appear per problem opened, on what share of opens
anything appears, how many of the shown titles were ordered, and what share
of all ordered titles they covered.

Nothing is written, and no todo title is printed.
"""
import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from emr.todo_suggestions import MIN_ORDERS, MIN_PATIENTS, collect_units, replay

TOP = (1, 3, 5)
CUTOFFS = (0.05, 0.10, 0.20)


def _percent(part, whole):
    return f'{100.0 * part / whole:5.1f}%' if whole else '   n/a'


class Command(BaseCommand):
    help = 'Replay suggested todos over past visits and report how often they were right.'

    def add_arguments(self, parser):
        parser.add_argument('--since', default='2025-01-01',
                            help='First day of the test period (YYYY-MM-DD). Earlier visits only teach.')
        parser.add_argument('--physician', type=int, action='append', dest='physicians',
                            help='Limit to this physician user id (repeatable).')
        parser.add_argument('--min-orders', type=int, default=MIN_ORDERS)
        parser.add_argument('--min-patients', type=int, default=MIN_PATIENTS)

    def handle(self, *args, **options):
        try:
            day = datetime.date.fromisoformat(options['since'])
        except ValueError:
            raise CommandError('--since must be a date, YYYY-MM-DD')
        since = timezone.make_aware(datetime.datetime.combine(day, datetime.time.min))

        units = collect_units(options['physicians'])
        if not units:
            self.stdout.write('No finished visits found.')
            return
        result = replay(units, since, CUTOFFS, TOP, options['min_orders'], options['min_patients'])

        out = self.stdout.write
        out('=== Replay of suggested todos ===')
        out(f"test period     : visits from {day.isoformat()}")
        out(f"history         : {len(units)} problem opens in "
            f"{len({unit.encounter_id for unit in units})} visits, from {units[0].started.date().isoformat()}")
        out(f"problem opens   : {result['opens']}  ({_percent(result['opens_with_an_order'], result['opens'])} followed by an order)")
        out(f"ordered titles  : {result['ordered_titles']}")
        out('')
        out('Exact title among the k most often ordered on that kind of problem')
        for k in TOP:
            out(f"  top {k}         : {_percent(result['hits'][k], result['ordered_titles'])}")
        out('')
        out(f"What the app would show (at most 3; floor {options['min_orders']} orders, "
            f"{options['min_patients']} patients)")
        out('  cutoff   shown per open   opens showing any   shown that were ordered   ordered titles covered')
        for cutoff in CUTOFFS:
            bucket = result['policy'][cutoff]
            per_open = bucket['shown'] / result['opens'] if result['opens'] else 0.0
            out(f"  {cutoff:>5.2f}   {per_open:>14.2f}   "
                f"{_percent(bucket['opens_showing'], result['opens']):>17}   "
                f"{_percent(bucket['shown_and_ordered'], bucket['shown']):>22}   "
                f"{_percent(bucket['shown_and_ordered'], result['ordered_titles']):>22}")
