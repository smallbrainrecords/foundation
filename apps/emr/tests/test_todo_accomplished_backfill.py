"""`backfill_todo_accomplished_at` — completion times recovered from the log.

The shapes below are the ones found in the 2026-07-22 copy of production:
  * stamp == created_on  — migration 0177's approximation (69,828 todos);
  * stamp NULL           — todos created before 2017-03-14 (11,379);
  * a real stamp         — completed through the mobile API since 2026-06-11.

TransactionTestCase, not TestCase: the command creates its undo table with DDL,
which commits implicitly on MySQL.
"""
from datetime import datetime, timezone as dt_tz
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TransactionTestCase

from emr.management.commands import backfill_todo_accomplished_at as command
from emr.models import PatientMutationStamp, ToDo, TodoActivity, UserProfile

LEGACY_DONE = 'Updated status of this todo to <b>accomplished</b>.'
LEGACY_UNDONE = 'Updated status of this todo to <b>not accomplished</b>.'
MOBILE_DONE = 'Updated status to accomplished'
MOBILE_UNDONE = 'Updated status to not accomplished'


def at(year, month=1, day=1, hour=12):
    return datetime(year, month, day, hour, 0, 0, tzinfo=dt_tz.utc)


class BackfillTodoAccomplishedAtTests(TransactionTestCase):

    def setUp(self):
        self._drop_backup()
        self.patient = User.objects.create_user(username='pt')
        UserProfile.objects.create(user=self.patient, role='patient')

    def tearDown(self):
        self._drop_backup()

    @staticmethod
    def _drop_backup():
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS {command.BACKUP_TABLE}')

    # -- fixtures ---------------------------------------------------------

    def todo(self, *, accomplished=True, created_on=None, accomplished_at=None, patient=None):
        """A todo in exactly the stored shape asked for. `.update()` because
        both timestamps are otherwise computed on save."""
        row = ToDo.objects.create(patient=patient or self.patient, todo='order')
        ToDo.objects.filter(pk=row.pk).update(
            accomplished=accomplished, created_on=created_on, accomplished_at=accomplished_at)
        return row

    def event(self, todo, text, when):
        row = TodoActivity.objects.create(todo=todo, activity=text)
        TodoActivity.objects.filter(pk=row.pk).update(created_on=when)

    def stored(self, todo):
        return ToDo.objects.values_list('accomplished_at', flat=True).get(pk=todo.pk)

    def run_command(self, *args):
        out = StringIO()
        call_command('backfill_todo_accomplished_at', *args, '--pause', '0', stdout=out)
        return out.getvalue()

    def backup_rows(self):
        with connection.cursor() as cursor:
            cursor.execute(
                f'SELECT todo_id, old_accomplished_at, new_accomplished_at FROM {command.BACKUP_TABLE}')
            return cursor.fetchall()

    # -- the three stored shapes -------------------------------------------

    def test_creation_stamp_is_replaced_by_the_completion_event(self):
        todo = self.todo(created_on=at(2024, 3, 1), accomplished_at=at(2024, 3, 1))
        self.event(todo, LEGACY_DONE, at(2025, 11, 20))

        self.run_command('--apply')

        self.assertEqual(self.stored(todo), at(2025, 11, 20))

    def test_a_todo_with_no_stamp_at_all_is_filled(self):
        # Created before 2017-03-14: no created_on, so migration 0177 left it NULL.
        todo = self.todo(created_on=None, accomplished_at=None)
        self.event(todo, LEGACY_DONE, at(2018, 6, 4))

        self.run_command('--apply')

        self.assertEqual(self.stored(todo), at(2018, 6, 4))

    def test_a_real_stamp_is_never_touched(self):
        todo = self.todo(created_on=at(2026, 6, 1), accomplished_at=at(2026, 6, 20))
        self.event(todo, MOBILE_DONE, at(2026, 6, 25))

        self.run_command('--apply')

        self.assertEqual(self.stored(todo), at(2026, 6, 20))

    # -- which event --------------------------------------------------------

    def test_the_latest_completion_wins_across_both_sentences(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2024, 2, 1))
        self.event(todo, LEGACY_UNDONE, at(2024, 3, 1))
        self.event(todo, MOBILE_DONE, at(2026, 7, 1))

        self.run_command('--apply')

        self.assertEqual(self.stored(todo), at(2026, 7, 1))

    def test_un_completed_after_its_last_completion_is_left_alone(self):
        # Accomplished now, but the last thing logged was "not accomplished":
        # it was completed again by a path that wrote no row, so the logged
        # completion is too early to be true.
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2024, 2, 1))
        self.event(todo, LEGACY_UNDONE, at(2024, 3, 1))

        out = self.run_command('--apply')

        self.assertEqual(self.stored(todo), at(2024, 1, 1))
        self.assertIn('un-completed after its last completion event', out)

    def test_nothing_is_written_without_a_completion_event(self):
        legacy = self.todo(created_on=None, accomplished_at=None)
        created = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(created, 'Added this todo.', at(2024, 1, 1))

        self.run_command('--apply')

        self.assertIsNone(self.stored(legacy))
        self.assertEqual(self.stored(created), at(2024, 1, 1))

    def test_an_event_that_is_not_later_never_moves_a_date_earlier(self):
        todo = self.todo(created_on=at(2024, 5, 1), accomplished_at=at(2024, 5, 1))
        self.event(todo, LEGACY_DONE, at(2024, 4, 1))

        self.run_command('--apply')

        self.assertEqual(self.stored(todo), at(2024, 5, 1))

    def test_an_open_todo_is_never_dated(self):
        todo = self.todo(accomplished=False, created_on=at(2024, 1, 1), accomplished_at=None)
        self.event(todo, LEGACY_DONE, at(2024, 2, 1))

        self.run_command('--apply')

        self.assertIsNone(self.stored(todo))

    # -- modes ----------------------------------------------------------------

    def test_dry_run_reports_and_writes_nothing(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2025, 12, 1))

        out = self.run_command()

        self.assertEqual(self.stored(todo), at(2024, 1, 1))
        self.assertIn('dry-run', out)
        self.assertIn('will correct (created -> event): 1', out)
        self.assertNotIn(command.BACKUP_TABLE, connection.introspection.table_names())

    def test_a_second_run_writes_nothing(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2025, 12, 1))
        self.run_command('--apply')

        out = self.run_command('--apply')

        self.assertIn('rows written            : 0', out)
        self.assertEqual(self.stored(todo), at(2025, 12, 1))

    def test_limit_writes_only_the_first_slice_by_id(self):
        todos = []
        for _ in range(3):
            row = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
            self.event(row, LEGACY_DONE, at(2025, 12, 1))
            todos.append(row)

        self.run_command('--apply', '--limit', '2')

        self.assertEqual([self.stored(t) for t in todos],
                         [at(2025, 12, 1), at(2025, 12, 1), at(2024, 1, 1)])

    def test_rows_changed_after_the_plan_was_made_are_left_alone(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2025, 12, 1))
        writes, _, _ = command.build_plan()
        # Someone toggles it between the plan and the write: a real stamp now.
        ToDo.objects.filter(pk=todo.pk).update(accomplished_at=at(2026, 8, 1))

        written, _ = command.apply_writes(writes)

        self.assertEqual(written, 0)
        self.assertEqual(self.stored(todo), at(2026, 8, 1))

    # -- undo -------------------------------------------------------------------

    def test_rollback_restores_what_the_run_replaced(self):
        created = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(created, LEGACY_DONE, at(2025, 12, 1))
        legacy = self.todo(created_on=None, accomplished_at=None)
        self.event(legacy, LEGACY_DONE, at(2018, 6, 4))
        self.run_command('--apply')
        self.assertEqual(
            {(r[0], r[1], r[2]) for r in self.backup_rows()},
            {(created.pk, datetime(2024, 1, 1, 12), datetime(2025, 12, 1, 12)),
             (legacy.pk, None, datetime(2018, 6, 4, 12))})

        self.run_command('--rollback')

        self.assertEqual(self.stored(created), at(2024, 1, 1))
        self.assertIsNone(self.stored(legacy))

    def test_rollback_leaves_a_later_real_completion_alone(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2025, 12, 1))
        self.run_command('--apply')
        # Completed again after the backfill: a real stamp the command never wrote.
        ToDo.objects.filter(pk=todo.pk).update(accomplished_at=at(2026, 9, 9))

        self.run_command('--rollback')

        self.assertEqual(self.stored(todo), at(2026, 9, 9))

    def test_rollback_with_nothing_to_undo_says_so(self):
        with self.assertRaises(CommandError):
            self.run_command('--rollback')

    def test_the_original_value_survives_a_rerun_of_the_backup(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2025, 12, 1))
        self.run_command('--apply')
        # A newer completion event appears and the command runs again: the
        # row is no longer a candidate, and the backup keeps the ORIGINAL old.
        self.event(todo, LEGACY_DONE, at(2026, 1, 1))
        self.run_command('--apply')

        self.assertEqual(
            [(r[0], r[1]) for r in self.backup_rows()], [(todo.pk, datetime(2024, 1, 1, 12))])

    # -- charts refresh -------------------------------------------------------------

    def test_affected_patients_are_stamped_so_open_charts_pull(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        self.event(todo, LEGACY_DONE, at(2025, 12, 1))
        untouched = User.objects.create_user(username='other')
        UserProfile.objects.create(user=untouched, role='patient')
        self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1), patient=untouched)

        self.run_command('--apply')

        self.assertTrue(PatientMutationStamp.objects.filter(patient=self.patient).exists())
        self.assertFalse(PatientMutationStamp.objects.filter(patient=untouched).exists())

    def test_output_names_no_patient_and_no_todo_text(self):
        todo = self.todo(created_on=at(2024, 1, 1), accomplished_at=at(2024, 1, 1))
        ToDo.objects.filter(pk=todo.pk).update(todo='colonoscopy for Jane Doe')
        self.event(todo, LEGACY_DONE, at(2025, 12, 1))

        out = self.run_command('--apply')

        self.assertNotIn('Jane', out)
        self.assertNotIn('colonoscopy', out)
        self.assertNotIn(self.patient.username, out)

    # -- the sentences ----------------------------------------------------------------

    def test_the_sentences_are_the_four_the_writers_log(self):
        self.assertEqual(set(command.DONE_ACTIVITIES), {LEGACY_DONE, MOBILE_DONE})
        self.assertEqual(set(command.UNDONE_ACTIVITIES), {LEGACY_UNDONE, MOBILE_UNDONE})
