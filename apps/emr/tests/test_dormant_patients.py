"""`inactivate_dormant_patients` — patients with no encounter in N years.

Owner request 2026-11-19: "make any patient who has not had an appointment in
the past 7 years inactive"; an encounter is an appointment.

TransactionTestCase, not TestCase: the command creates its undo table with DDL,
which commits implicitly on MySQL.
"""
from datetime import datetime, timedelta, timezone as dt_tz
from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone

from emr.management.commands import inactivate_dormant_patients as command
from emr.models import Encounter, UserProfile


def years_ago(n, days=0):
    return timezone.now() - timedelta(days=round(365.25 * n) + days)


class DormantPatientsFixtures(TransactionTestCase):
    """Shared fixtures; holds no tests of its own."""

    def setUp(self):
        self._drop_backup()
        self.physician = self.person('doc', role='physician', joined=years_ago(12))

    def tearDown(self):
        self._drop_backup()

    @staticmethod
    def _drop_backup():
        with connection.cursor() as cursor:
            cursor.execute(f'DROP TABLE IF EXISTS {command.BACKUP_TABLE}')

    # -- fixtures ---------------------------------------------------------

    def person(self, username, *, role='patient', joined=None, active=True):
        user = User.objects.create_user(username=username)
        UserProfile.objects.create(user=user, role=role)
        User.objects.filter(pk=user.pk).update(
            date_joined=joined or years_ago(10), is_active=active)
        return user

    def visit(self, patient, when):
        """An encounter that started at `when` (`starttime` is auto_now_add)."""
        row = Encounter.objects.create(physician=self.physician, patient=patient)
        Encounter.objects.filter(pk=row.pk).update(starttime=when)
        return row

    def is_active(self, user):
        return User.objects.values_list('is_active', flat=True).get(pk=user.pk)

    def run_command(self, *args):
        out = StringIO()
        call_command('inactivate_dormant_patients', *args, '--pause', '0', stdout=out)
        return out.getvalue()

    def backup_ids(self):
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT user_id FROM {command.BACKUP_TABLE} ORDER BY user_id')
            return [row[0] for row in cursor.fetchall()]


class InactivateDormantPatientsTests(DormantPatientsFixtures):

    # -- who is switched off ------------------------------------------------

    def test_a_patient_last_seen_eight_years_ago_is_made_inactive(self):
        patient = self.person('old')
        self.visit(patient, years_ago(8))

        self.run_command('--apply')

        self.assertFalse(self.is_active(patient))

    def test_a_patient_seen_within_seven_years_stays_active(self):
        patient = self.person('recent')
        self.visit(patient, years_ago(9))
        self.visit(patient, years_ago(6, days=300))

        self.run_command('--apply')

        self.assertTrue(self.is_active(patient))

    def test_the_latest_encounter_decides_not_the_first(self):
        patient = self.person('returning')
        self.visit(patient, years_ago(1))
        self.visit(patient, years_ago(9))

        self.run_command('--apply')

        self.assertTrue(self.is_active(patient))

    def test_an_old_patient_with_no_encounter_at_all_is_made_inactive(self):
        patient = self.person('never', joined=years_ago(11))

        self.run_command('--apply')

        self.assertFalse(self.is_active(patient))

    def test_a_patient_added_within_the_window_is_left_alone(self):
        # A new patient waiting for a first visit has no encounter at all.
        patient = self.person('new', joined=years_ago(0, days=20))

        out = self.run_command('--apply')

        self.assertTrue(self.is_active(patient))
        self.assertIn('account created within the window', out)

    def test_include_new_also_switches_off_patients_added_within_the_window(self):
        patient = self.person('new', joined=years_ago(3))

        self.run_command('--apply', '--include-new')

        self.assertFalse(self.is_active(patient))

    def test_staff_accounts_are_never_touched(self):
        nurse = self.person('nurse', role='nurse', joined=years_ago(15))

        self.run_command('--apply')

        self.assertTrue(self.is_active(nurse))
        self.assertTrue(self.is_active(self.physician))

    def test_a_patient_already_inactive_is_not_recorded(self):
        patient = self.person('gone', active=False)

        self.run_command('--apply')

        self.assertFalse(self.is_active(patient))
        self.assertEqual(self.backup_ids(), [])

    def test_years_sets_the_window(self):
        patient = self.person('mid')
        self.visit(patient, years_ago(4))

        self.run_command('--apply', '--years', '3')

        self.assertFalse(self.is_active(patient))

    def test_years_below_one_is_refused(self):
        with self.assertRaises(CommandError):
            self.run_command('--years', '0')

    # -- dry run, canary, undo ----------------------------------------------

    def test_the_dry_run_writes_nothing(self):
        patient = self.person('old')
        self.visit(patient, years_ago(8))

        out = self.run_command()

        self.assertTrue(self.is_active(patient))
        self.assertNotIn(command.BACKUP_TABLE, connection.introspection.table_names())
        self.assertIn('will make inactive                : 1', out)
        self.assertIn('Dry run', out)

    def test_the_report_names_patients_still_being_charted(self):
        from emr.models import ToDo
        patient = self.person('old')
        self.visit(patient, years_ago(8))
        ToDo.objects.create(patient=patient, todo='refill')

        out = self.run_command()

        self.assertIn('with a todo or document added in the past 12 months: 1', out)
        self.assertIn(f'patient ids: {patient.pk}', out)

    def test_limit_switches_off_only_the_first_patients_by_id(self):
        first, second = self.person('a'), self.person('b')

        self.run_command('--apply', '--limit', '1')

        self.assertFalse(self.is_active(first))
        self.assertTrue(self.is_active(second))
        self.assertEqual(self.backup_ids(), [first.pk])

    def test_a_patient_seen_after_the_plan_was_made_is_left_alone(self):
        patient = self.person('old')
        self.visit(patient, years_ago(8))
        cutoff = command.cutoff_for(timezone.now(), 7)
        plan, _ = command.build_plan(cutoff)
        self.visit(patient, timezone.now())

        written = command.apply_inactivation(plan, cutoff)

        self.assertEqual(written, 0)
        self.assertTrue(self.is_active(patient))
        self.assertEqual(self.backup_ids(), [])

    def test_rollback_makes_the_switched_off_patients_active_again(self):
        old = self.person('old')
        self.visit(old, years_ago(8))
        by_hand = self.person('by-hand', active=False)

        self.run_command('--apply')
        self.assertFalse(self.is_active(old))
        out = self.run_command('--rollback')

        self.assertTrue(self.is_active(old))
        self.assertFalse(self.is_active(by_hand))
        self.assertIn('patients made active again : 1', out)

    def test_a_second_run_finds_nothing_to_do(self):
        self.person('old')
        self.run_command('--apply')

        out = self.run_command('--apply')

        self.assertIn('patients made inactive  : 0', out)

    def test_rollback_without_a_record_is_refused(self):
        with self.assertRaises(CommandError):
            self.run_command('--rollback')

    def test_the_cutoff_is_calendar_years(self):
        now = datetime(2026, 11, 19, 15, 0, tzinfo=dt_tz.utc)
        self.assertEqual(command.cutoff_for(now, 7), datetime(2019, 11, 19, 15, 0, tzinfo=dt_tz.utc))
        leap = datetime(2028, 2, 29, 12, 0, tzinfo=dt_tz.utc)
        self.assertEqual(command.cutoff_for(leap, 7), datetime(2021, 2, 28, 12, 0, tzinfo=dt_tz.utc))


class SpareChartedPatientsTests(DormantPatientsFixtures):
    """`--spare-charted`: a dormant patient whose chart got a todo or a
    document in the past 12 months is left alone (owner decision 2026-11-19)."""

    def todo(self, patient, when):
        from emr.models import ToDo
        row = ToDo.objects.create(patient=patient, todo='refill')
        ToDo.objects.filter(pk=row.pk).update(created_on=when)

    def document(self, patient, when):
        from emr.models import Document
        row = Document.objects.create(author=self.physician, patient=patient, document_name='fax')
        Document.objects.filter(pk=row.pk).update(created_on=when)

    def test_a_recent_todo_spares_the_patient(self):
        patient = self.person('charted')
        self.visit(patient, years_ago(8))
        self.todo(patient, years_ago(0, days=30))

        out = self.run_command('--apply', '--spare-charted')

        self.assertTrue(self.is_active(patient))
        self.assertIn(f'left active: {command.SPARED_REASON}', out)

    def test_a_recent_document_spares_the_patient(self):
        patient = self.person('faxed')
        self.document(patient, years_ago(0, days=200))

        self.run_command('--apply', '--spare-charted')

        self.assertTrue(self.is_active(patient))

    def test_without_the_option_a_charted_patient_is_switched_off(self):
        patient = self.person('charted')
        self.todo(patient, years_ago(0, days=30))

        self.run_command('--apply')

        self.assertFalse(self.is_active(patient))

    def test_chart_activity_older_than_a_year_spares_nothing(self):
        patient = self.person('stale')
        self.todo(patient, years_ago(2))
        self.document(patient, years_ago(1, days=10))

        self.run_command('--apply', '--spare-charted')

        self.assertFalse(self.is_active(patient))

    def test_spared_and_dormant_patients_are_told_apart(self):
        charted, dormant = self.person('charted'), self.person('dormant')
        self.todo(charted, years_ago(0, days=5))

        self.run_command('--apply', '--spare-charted')

        self.assertTrue(self.is_active(charted))
        self.assertFalse(self.is_active(dormant))
        self.assertEqual(self.backup_ids(), [dormant.pk])

    def test_a_patient_charted_after_the_plan_was_made_is_left_alone(self):
        patient = self.person('old')
        now = timezone.now()
        cutoff = command.cutoff_for(now, 7)
        since = now - command.CHARTED_WINDOW
        plan, _ = command.build_plan(cutoff, charted_since=since)
        self.todo(patient, timezone.now())

        written = command.apply_inactivation(plan, cutoff, charted_since=since)

        self.assertEqual(written, 0)
        self.assertTrue(self.is_active(patient))
