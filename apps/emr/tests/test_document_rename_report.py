"""`report_document_renames` — the read-only data for the auto-namer review.

Rows are written the way the mobile endpoints write them: one
`Renamed document: <old> -> <new>` row per linked problem, or one row with
`problem=None` when the document has no links (every rename made at assign).
Times are set explicitly because `created_on` is `auto_now_add`.
"""
import json
from datetime import datetime, timedelta, timezone as dt_tz
from io import StringIO
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.utils import OperationalError
from django.test import TestCase, TransactionTestCase

from emr.management.commands import report_document_renames as command
from emr.models import Document, Problem, ProblemActivity, UserProfile

SINCE = '2026-09-01'
UNTIL = '2026-10-01'


def at(day, hour=12, second=0):
    return datetime(2026, 9, day, hour, 0, second, tzinfo=dt_tz.utc)


class DocumentRenameReportTests(TestCase):

    def setUp(self):
        self.staff = self.user('nurse', 'nurse')
        self.patient = self.user('pt1', 'patient')
        self.other_patient = self.user('pt2', 'patient')
        self.team = self.user('doc', 'physician')

    def user(self, name, role):
        user = User.objects.create_user(username=name)
        UserProfile.objects.create(user=user, role=role)
        return user

    def document(self, created, name, arrival='scan.pdf', patient='default', team=None):
        doc = Document.objects.create(
            document_name=name, author=self.staff,
            patient=self.patient if patient == 'default' else patient,
            team=team, original_file_name=arrival,
        )
        Document.objects.filter(pk=doc.pk).update(created_on=created)
        return doc

    def rename(self, when, old, new, problems=(None,), author=None):
        for problem in problems:
            row = ProblemActivity.objects.create(
                problem=problem, author=author or self.staff,
                activity=f'Renamed document: {old} -> {new}',
            )
            ProblemActivity.objects.filter(pk=row.pk).update(created_on=when)

    def added(self, when, name, author=None):
        """The row a chart upload writes in its own request (and assign
        writes later, by whoever assigns)."""
        row = ProblemActivity.objects.create(
            problem=None, author=author or self.staff, activity=f'Added document: {name}')
        ProblemActivity.objects.filter(pk=row.pk).update(created_on=when)

    def problem(self, patient=None):
        return Problem.objects.create(patient=patient or self.patient, problem_name='Hypertension')

    def run_report(self, *extra):
        out = StringIO()
        call_command('report_document_renames', '--since', SINCE, '--until', UNTIL, *extra, stdout=out)
        lines = [json.loads(line) for line in out.getvalue().splitlines()]
        renames = [line for line in lines if line['kind'] == 'rename']
        documents = {line['id']: line for line in lines if line['kind'] == 'document'}
        return renames, documents, lines[-1]

    # MARK: - Renames

    def test_rows_fanned_out_to_linked_problems_are_one_rename(self):
        first, second = self.problem(), self.problem()
        self.rename(at(5), 'CBC', 'CBC, CMP', problems=(first, second))

        renames, _, summary = self.run_report()

        self.assertEqual(len(renames), 1)
        self.assertEqual(renames[0]['old'], 'CBC')
        self.assertEqual(renames[0]['new'], 'CBC, CMP')
        self.assertEqual(renames[0]['scope'], 'problem')
        self.assertEqual(renames[0]['problem_ids'], sorted([first.id, second.id]))
        self.assertEqual(renames[0]['patient_id'], self.patient.id)
        self.assertEqual(summary['renames'], 1)

    def test_an_unlinked_rename_has_no_patient(self):
        self.rename(at(5), 'MRI', 'MRI Brain')

        renames, _, summary = self.run_report()

        self.assertEqual(renames[0]['scope'], 'unlinked')
        self.assertIsNone(renames[0]['patient_id'])
        self.assertEqual(summary['renames_unlinked'], 1)

    def test_the_same_rename_twice_far_apart_is_two_renames(self):
        self.rename(at(5), 'scan', 'labs')
        self.rename(at(6), 'scan', 'labs')

        renames, _, _ = self.run_report()

        self.assertEqual(len(renames), 2)

    def test_renames_outside_the_window_are_left_out(self):
        self.rename(datetime(2026, 8, 31, 23, 59, tzinfo=dt_tz.utc), 'a', 'b')
        self.rename(datetime(2026, 10, 1, 0, 0, tzinfo=dt_tz.utc), 'c', 'd')
        ProblemActivity.objects.create(problem=None, author=self.staff, activity='Added document: CBC')

        renames, _, _ = self.run_report()

        self.assertEqual(renames, [])

    # MARK: - Documents

    def test_an_auto_named_document_nobody_renamed_was_kept(self):
        doc = self.document(at(3), 'CBC, CMP')

        _, documents, summary = self.run_report()

        line = documents[doc.id]
        self.assertTrue(line['auto_named'])
        self.assertFalse(line['renamed'])
        self.assertEqual(line['first_name'], 'CBC, CMP')
        self.assertEqual(line['match'], 'none')
        self.assertEqual(summary['auto_named'], 1)
        self.assertEqual(summary['auto_named_kept'], 1)

    def test_an_auto_name_replaced_at_assign_is_traced(self):
        doc = self.document(at(3), 'labs')
        self.rename(at(4), 'CBC, CMP', 'labs')

        renames, documents, summary = self.run_report()

        line = documents[doc.id]
        self.assertEqual(line['first_name'], 'CBC, CMP')
        self.assertTrue(line['auto_named'])
        self.assertTrue(line['renamed'])
        self.assertEqual(line['match'], 'traced')
        self.assertEqual(line['renames'], [renames[0]['n']])
        self.assertEqual(renames[0]['documents'], [doc.id])
        self.assertEqual(summary['auto_named_renamed'], 1)

    def test_a_chain_of_renames_is_walked_back_to_the_first_name(self):
        doc = self.document(at(3), 'MRI head')
        self.rename(at(4), 'MRI', 'MRI Brain')
        self.rename(at(6), 'MRI Brain', 'MRI head', problems=(self.problem(),))

        _, documents, _ = self.run_report()

        line = documents[doc.id]
        self.assertEqual(line['first_name'], 'MRI')
        self.assertEqual(len(line['renames']), 2)

    def test_renaming_back_and_forth_is_followed(self):
        doc = self.document(at(3), 'B')
        self.rename(at(4), 'A', 'B')
        self.rename(at(5), 'B', 'A')
        self.rename(at(6), 'A', 'B')

        _, documents, _ = self.run_report()

        self.assertEqual(documents[doc.id]['first_name'], 'A')
        self.assertEqual(len(documents[doc.id]['renames']), 3)

    def test_a_document_that_kept_its_arrival_name_is_not_auto_named(self):
        doc = self.document(at(3), 'echo', arrival='scan.pdf')
        self.rename(at(4), 'scan', 'echo')

        _, documents, summary = self.run_report()

        self.assertFalse(documents[doc.id]['auto_named'])
        self.assertEqual(documents[doc.id]['first_name'], 'scan')
        self.assertEqual(summary['auto_named'], 0)
        self.assertEqual(summary['pool_not_auto_named_renamed'], 1)

    def test_without_an_arrival_name_auto_naming_is_unknown(self):
        doc = self.document(at(3), 'CBC', arrival=None)

        _, documents, summary = self.run_report()

        self.assertIsNone(documents[doc.id]['auto_named'])
        self.assertEqual(summary['with_arrival_name'], 0)
        self.assertEqual(summary['auto_named'], 0)

    def test_a_rename_before_the_document_existed_is_not_its_own(self):
        self.rename(at(2), 'CMP', 'CBC')
        doc = self.document(at(3), 'CBC')

        _, documents, _ = self.run_report()

        self.assertFalse(documents[doc.id]['renamed'])

    def test_a_linked_rename_on_another_chart_is_not_claimed(self):
        doc = self.document(at(3), 'CBC')
        self.rename(at(4), 'CMP', 'CBC', problems=(self.problem(self.other_patient),))

        _, documents, summary = self.run_report()

        self.assertFalse(documents[doc.id]['renamed'])
        self.assertEqual(summary['renames_unclaimed'], 1)

    def test_one_rename_two_documents_could_own_is_ambiguous_for_both(self):
        renamed = self.document(at(3), 'CBC', arrival='a.pdf')
        kept = self.document(at(3, hour=13), 'CBC', arrival='b.pdf', patient=self.other_patient)
        self.rename(at(4), 'CMP', 'CBC')

        _, documents, summary = self.run_report()

        self.assertEqual(documents[renamed.id]['match'], 'ambiguous')
        self.assertEqual(documents[kept.id]['match'], 'ambiguous')
        self.assertEqual(summary['ambiguous'], 2)
        self.assertEqual(summary['auto_named'], 0)

    def test_an_older_document_can_claim_a_rename_but_is_not_reported(self):
        older = self.document(datetime(2026, 8, 20, tzinfo=dt_tz.utc), 'CBC', arrival='a.pdf')
        newer = self.document(at(3), 'CBC', arrival='b.pdf')
        self.rename(at(4), 'CMP', 'CBC')

        _, documents, _ = self.run_report()

        self.assertNotIn(older.id, documents)
        self.assertEqual(documents[newer.id]['match'], 'ambiguous')

        # With no lookback the older document takes no part.
        _, documents, _ = self.run_report('--lookback-days', '0')
        self.assertEqual(documents[newer.id]['match'], 'traced')

    def test_a_name_containing_an_arrow_is_still_traced(self):
        doc = self.document(at(3), 'R -> L knee')
        self.rename(at(4), 'X-Ray Knee', 'R -> L knee')

        _, documents, _ = self.run_report()

        self.assertEqual(documents[doc.id]['first_name'], 'X-Ray Knee')

    def test_a_document_still_in_the_pool_is_reported_as_such(self):
        doc = self.document(at(3), 'CBC', patient=None, team=self.team)

        _, documents, summary = self.run_report()

        self.assertTrue(documents[doc.id]['in_pool'])
        self.assertIsNone(documents[doc.id]['patient_id'])
        self.assertEqual(summary['still_in_pool'], 1)

    # MARK: - Anchors, the pool, and where a document was uploaded

    def test_a_rename_from_an_arrival_name_belongs_to_that_document(self):
        """The first production run pinned the latest of 25 renames to "phq"
        on every document named "phq". Each rename's old name is its own
        document's scanner stamp."""
        renamed = self.document(at(3), 'phq', arrival='2026_09_03_09_11_16.pdf')
        typed = self.document(at(3, hour=13), 'phq', arrival='2026_09_03_09_50_18.pdf')
        self.added(at(3, hour=13), 'phq')
        self.rename(at(4), '2026_09_03_09_11_16', 'phq')

        renames, documents, summary = self.run_report()

        self.assertTrue(renames[0]['anchored'])
        self.assertEqual(renames[0]['documents'], [renamed.id])
        self.assertEqual(documents[renamed.id]['match'], 'traced')
        self.assertEqual(documents[renamed.id]['first_name'], '2026_09_03_09_11_16')
        self.assertFalse(documents[renamed.id]['auto_named'])
        self.assertEqual(documents[typed.id]['match'], 'none')
        self.assertEqual(documents[typed.id]['origin'], 'chart')
        self.assertTrue(documents[typed.id]['named_before_upload'])
        self.assertFalse(documents[typed.id]['auto_named'])
        self.assertEqual(summary['ambiguous'], 0)
        self.assertEqual(summary['renames_anchored'], 1)
        self.assertEqual(summary['chart_named_before_upload'], 1)
        self.assertEqual(summary['auto_named'], 0)

    def test_a_rename_from_a_chart_uploads_creation_name_belongs_to_it(self):
        """The 2026-10-20 run's largest ambiguous groups: a document uploaded
        in June or July (no arrival name recorded then) renamed this month to
        a name newer documents also carry. Its upload row names it, and the
        default lookback reaches back that far."""
        june = datetime(2026, 6, 20, 12, tzinfo=dt_tz.utc)
        older = self.document(june, 'CBC', arrival=None)
        self.added(june, 'Kelly Ryan 2026-06-20 12-00')
        newer = self.document(at(3), 'CBC', arrival='b.pdf')
        self.rename(at(4), 'Kelly Ryan 2026-06-20 12-00', 'CBC')

        renames, documents, summary = self.run_report()

        self.assertTrue(renames[0]['anchored'])
        self.assertEqual(renames[0]['documents'], [older.id])
        self.assertEqual(documents[newer.id]['match'], 'none')
        self.assertEqual(summary['auto_named_kept'], 1)

        # With a 30-day lookback the June document takes no part, and the
        # newer one is handed its rename.
        renames, documents, _ = self.run_report('--lookback-days', '30')
        self.assertFalse(renames[0]['anchored'])
        self.assertEqual(documents[newer.id]['match'], 'traced')

    def test_a_document_still_in_the_pool_never_claims_a_rename(self):
        waiting = self.document(at(3), 'CBC', arrival='a.pdf', patient=None, team=self.team)
        assigned = self.document(at(3, hour=13), 'CBC', arrival='b.pdf')
        self.rename(at(4), 'CMP', 'CBC')

        _, documents, summary = self.run_report()

        self.assertEqual(documents[waiting.id]['match'], 'none')
        self.assertEqual(documents[assigned.id]['match'], 'traced')
        self.assertEqual(documents[assigned.id]['first_name'], 'CMP')
        self.assertEqual(summary['auto_named_renamed'], 1)
        self.assertEqual(summary['auto_named_still_in_pool'], 1)
        self.assertEqual(summary['ambiguous'], 0)

    def test_an_added_row_by_the_uploader_at_creation_marks_a_chart_upload(self):
        chart = self.document(at(3), 'CBC', arrival='a.pdf')
        self.added(at(3, second=1), 'CBC')
        pool = self.document(at(3, hour=13), 'CMP', arrival='b.pdf')
        # Assign writes its own row, later and by whoever assigned it.
        self.added(at(4), 'CMP', author=self.team)

        _, documents, summary = self.run_report()

        self.assertEqual(documents[chart.id]['origin'], 'chart')
        self.assertFalse(documents[chart.id]['auto_named'])
        self.assertEqual(documents[pool.id]['origin'], 'pool')
        self.assertTrue(documents[pool.id]['auto_named'])
        self.assertEqual(summary['from_chart'], 1)
        self.assertEqual(summary['from_pool'], 1)

    def test_a_chart_upload_is_traced_back_only_to_its_creation_name(self):
        doc = self.document(at(3), 'CBC', arrival='x.pdf')
        self.added(at(3), 'labs')
        self.rename(at(4), 'CMP', 'labs')   # some other document's
        self.rename(at(5), 'labs', 'CBC')

        renames, documents, _ = self.run_report()

        line = documents[doc.id]
        self.assertEqual(line['first_name'], 'labs')
        self.assertEqual(len(line['renames']), 1)
        self.assertEqual(line['match'], 'traced')
        unclaimed = [r for r in renames if not r['documents']]
        self.assertEqual([r['old'] for r in unclaimed], ['CMP'])

    def test_a_chart_upload_that_cannot_reach_its_creation_name_is_inconsistent(self):
        doc = self.document(at(3), 'CBC', arrival='x.pdf')
        self.added(at(3), 'labs')

        _, documents, summary = self.run_report()

        self.assertEqual(documents[doc.id]['match'], 'inconsistent')
        self.assertEqual(summary['inconsistent'], 1)

    # MARK: - Output

    def test_every_line_is_json_and_the_summary_is_last(self):
        self.document(at(3), 'CBC')
        self.rename(at(4), 'a', 'b')

        out = StringIO()
        call_command('report_document_renames', '--since', SINCE, '--until', UNTIL, stdout=out)
        kinds = [json.loads(line)['kind'] for line in out.getvalue().splitlines()]

        self.assertEqual(kinds, ['rename', 'document', 'summary'])

    def test_summary_only_prints_one_line(self):
        self.document(at(3), 'CBC')

        out = StringIO()
        call_command('report_document_renames', '--since', SINCE, '--until', UNTIL, '--summary-only', stdout=out)
        lines = out.getvalue().splitlines()

        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])['kind'], 'summary')

    def test_bad_arguments_are_refused(self):
        with self.assertRaises(CommandError):
            call_command('report_document_renames', '--since', '2026-10-01', '--until', '2026-09-01')
        with self.assertRaises(CommandError):
            call_command('report_document_renames', '--since', '1 Sept')

    def test_the_report_writes_nothing(self):
        self.document(at(3), 'labs')
        self.rename(at(4), 'CBC', 'labs')
        before = (Document.objects.count(), ProblemActivity.objects.count(),
                  list(Document.objects.values_list('document_name', flat=True)))

        self.run_report()

        after = (Document.objects.count(), ProblemActivity.objects.count(),
                 list(Document.objects.values_list('document_name', flat=True)))
        self.assertEqual(before, after)


class DocumentRenameReportReadOnlyTests(TransactionTestCase):
    """The session guard. TransactionTestCase because a TestCase runs the
    command inside a transaction that began read-write, where the session
    setting does not reach."""

    def test_a_write_during_the_report_is_refused_and_the_session_is_restored(self):
        if connection.vendor != 'mysql':
            self.skipTest('the READ ONLY session guard is MySQL-only')
        author = User.objects.create_user(username='nurse')

        def write_instead(self_, since, until, lookback):
            ProblemActivity.objects.create(problem=None, author=author, activity='should not land')
            return []

        with mock.patch.object(command.Command, 'report', write_instead):
            with self.assertRaises(OperationalError):
                call_command('report_document_renames', stdout=StringIO())

        self.assertFalse(ProblemActivity.objects.filter(activity='should not land').exists())
        # Restored: this session can write again.
        ProblemActivity.objects.create(problem=None, author=author, activity='after')
        self.assertTrue(ProblemActivity.objects.filter(activity='after').exists())
