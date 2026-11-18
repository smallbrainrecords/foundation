"""`emr.inbound_fax`: faxes the clinic line receives become pool documents,
once each, only after the start moment, and only when switched on.
RingCentral is replaced: no request leaves the test."""
import io
import json
import shutil
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from emr import inbound_fax
from emr import ringcentral_fax as rc
from emr.models import Document, InboundFax, UserProfile

PDF = b'%PDF-1.4 a fax from the lab'


def fax(i, received='2026-11-16T13:00:00Z', **extra):
    record = {
        'id': i, 'received': received, 'from_number': '+12315550140', 'from_name': 'NMRL',
        'to_numbers': [], 'to_keys': [], 'pages': 2, 'read_status': 'Read', 'message_status': 'Received',
        'availability': 'Alive',
        'attachments': [{'id': 900 + i, 'content_type': 'application/pdf', 'size': None}],
    }
    record.update(extra)
    return record


class _InboundFaxBase(TestCase):
    """RingCentral replaced, a team pool, the import switched on."""

    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        self.team = User.objects.create_user(username='ifax_doc', password='x')
        UserProfile.objects.create(user=self.team, role='physician')
        settings = override_settings(
            MEDIA_ROOT=media, INBOUND_FAX_ENABLED=True, INBOUND_FAX_TEAM_ID=self.team.id,
            INBOUND_FAX_START='2026-11-16T12:00:00Z')
        settings.enable()
        self.addCleanup(settings.disable)
        self.listed = []
        self.list_calls = 0
        self.downloads = []
        self.failures = {}
        self.body = PDF
        # RingCentral deletion: no permission unless a test grants it.
        self.granted = set()
        self.rc_deleted = []
        self.delete_failures = {}
        for patcher in (mock.patch.object(rc, 'is_configured', lambda: True),
                        mock.patch.object(rc, 'inbound_faxes', self._list),
                        mock.patch.object(rc, 'fax_attachment', self._download),
                        mock.patch.object(rc, 'granted_permissions', lambda: self.granted),
                        mock.patch.object(rc, 'move_fax_to_deleted', self._delete)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def _list(self, days=7, trace=None):
        self.list_calls += 1
        if trace is not None:
            trace.update(complete=True)
        return self.listed

    def _delete(self, message_id):
        self.rc_deleted.append(message_id)
        if message_id in self.delete_failures:
            raise self.delete_failures[message_id]

    def _download(self, message_id, attachment_id):
        self.downloads.append((message_id, attachment_id))
        if message_id in self.failures:
            raise self.failures[message_id]
        return self.body, 'application/pdf'


class InboundFaxImportTests(_InboundFaxBase):

    # Off unless configured

    def test_it_is_off_unless_every_setting_is_there(self):
        cases = [
            ({'INBOUND_FAX_ENABLED': False}, 'disabled'),
            ({'INBOUND_FAX_TEAM_ID': 0}, 'no_team'),
            ({'INBOUND_FAX_START': ''}, 'no_start'),
            ({'INBOUND_FAX_START': '2026-11-16T12:00:00'}, 'no_start'),  # no time zone
        ]
        for overrides, problem in cases:
            with self.subTest(problem=problem), override_settings(**overrides):
                self.assertEqual(inbound_fax.import_new_faxes(), {'configured': False, 'problem': problem})
        with mock.patch.object(rc, 'is_configured', lambda: False):
            self.assertEqual(inbound_fax.import_new_faxes()['problem'], 'no_credential')
        self.assertEqual(self.list_calls, 0)

    # Importing

    def test_new_faxes_become_documents_in_the_team_pool(self):
        self.listed = [fax(2, '2026-11-16T14:00:00Z'), fax(1)]
        summary = inbound_fax.import_new_faxes()
        self.assertEqual((summary['imported'], summary['listed'], summary['complete']), (2, 2, True))
        self.assertEqual(self.downloads, [('1', 901), ('2', 902)])  # oldest first
        row = InboundFax.objects.get(rc_message_id='1')
        doc = row.document
        self.assertIsNone(doc.patient)
        self.assertEqual((doc.team, doc.author), (self.team, self.team))
        self.assertEqual(doc.document_name, 'Fax from NMRL')
        self.assertEqual(doc.original_file_name, 'Fax from NMRL.pdf')
        self.assertEqual(doc.file_size, len(PDF))
        self.assertEqual(doc.client_uuid, inbound_fax.client_uuid_for('1'))
        with doc.document.open('rb') as stored:
            self.assertEqual(stored.read(), PDF)
        self.assertEqual((row.from_number, row.from_name, row.page_count), ('+12315550140', 'NMRL', 2))
        self.assertIsNotNone(row.imported_on)

    def test_faxes_received_before_the_start_are_never_imported(self):
        self.listed = [fax(1, '2026-11-16T11:59:59Z')]
        summary = inbound_fax.import_new_faxes()
        self.assertEqual((summary['listed'], summary['imported']), (0, 0))
        self.assertFalse(InboundFax.objects.exists())
        self.assertEqual(self.downloads, [])

    def test_a_second_pass_imports_nothing_again(self):
        self.listed = [fax(1), fax(2)]
        inbound_fax.import_new_faxes()
        summary = inbound_fax.import_new_faxes()
        self.assertEqual((summary['imported'], summary['already']), (0, 2))
        self.assertEqual(len(self.downloads), 2)
        self.assertEqual(Document.objects.filter(team=self.team).count(), 2)

    def test_a_deleted_fax_is_never_imported_again(self):
        # 2026-11-18: deleting a pool fax emptied InboundFax.document, and the
        # next pass fetched the fax again — 14 faxes came back in production,
        # one of them 7 times.
        self.listed = [fax(1), fax(2)]
        inbound_fax.import_new_faxes()
        doc = InboundFax.objects.get(rc_message_id='1').document
        doc.delete()
        self.assertIsNone(InboundFax.objects.get(rc_message_id='1').document_id)
        summary = inbound_fax.import_new_faxes()
        self.assertEqual((summary['imported'], summary['already'], summary['deleted']), (0, 1, 1))
        self.assertEqual(len(self.downloads), 2, 'nothing fetched again')
        self.assertEqual(Document.objects.filter(team=self.team).count(), 1)
        # The per-fax guard holds too, for a pass that reaches it directly.
        self.assertEqual(inbound_fax._import_one(fax(1), self.team, 'test'), 'deleted')
        self.assertEqual(len(self.downloads), 2)

    def test_a_pass_fetches_at_most_its_batch_and_leaves_the_rest_waiting(self):
        self.listed = [fax(1), fax(2, '2026-11-16T14:00:00Z'), fax(3, '2026-11-16T15:00:00Z')]
        first = inbound_fax.import_new_faxes(batch=2)
        self.assertEqual((first['imported'], first['waiting']), (2, 1))
        self.assertEqual([d[0] for d in self.downloads], ['1', '2'])
        second = inbound_fax.import_new_faxes(batch=2)
        self.assertEqual((second['imported'], second['already'], second['waiting']), (1, 2, 0))

    def test_a_failed_fetch_is_retried_then_given_up(self):
        self.listed = [fax(1)]
        self.failures['1'] = rc.FaxError('RingCentral did not send the fax: HTTP 500', 500)
        for attempt in range(1, inbound_fax.MAX_ATTEMPTS):
            summary = inbound_fax.import_new_faxes()
            self.assertEqual(summary['failed'], 1)
            self.assertEqual(InboundFax.objects.get(rc_message_id='1').attempts, attempt)
        summary = inbound_fax.import_new_faxes()
        self.assertEqual(summary['given_up'], 1)
        tries = len(self.downloads)
        summary = inbound_fax.import_new_faxes()
        self.assertEqual((summary['given_up'], len(self.downloads)), (1, tries))  # not asked again
        self.assertIn('HTTP 500', InboundFax.objects.get(rc_message_id='1').last_error)
        self.assertFalse(Document.objects.filter(team=self.team).exists())

    def test_too_many_requests_ends_the_pass_without_counting_against_the_fax(self):
        self.listed = [fax(1), fax(2, '2026-11-16T14:00:00Z')]
        self.failures['1'] = rc.FaxError('RingCentral did not send the fax: rate limit', 429)
        summary = inbound_fax.import_new_faxes()
        self.assertTrue(summary['rate_limited'])
        self.assertEqual((summary['imported'], summary['waiting']), (0, 2))
        self.assertEqual(InboundFax.objects.get(rc_message_id='1').attempts, 0)
        self.assertEqual(self.downloads, [('1', 901)])  # fax 2 was not tried

    def test_a_fax_with_no_pdf_is_given_up_with_the_reason(self):
        self.listed = [fax(1, attachments=[{'id': 5, 'content_type': 'image/tiff', 'size': None}])]
        summary = inbound_fax.import_new_faxes()
        self.assertEqual(summary['given_up'], 1)
        self.assertIn('image/tiff', InboundFax.objects.get(rc_message_id='1').last_error)
        self.assertEqual(self.downloads, [])

    def test_something_that_is_not_a_pdf_is_a_failure(self):
        self.listed = [fax(1)]
        self.body = b'<html>error</html>'
        summary = inbound_fax.import_new_faxes()
        self.assertEqual(summary['failed'], 1)
        self.assertIn('not a PDF', InboundFax.objects.get(rc_message_id='1').last_error)

    def test_the_name_falls_back_to_the_number_and_drops_odd_characters(self):
        self.assertEqual(inbound_fax.document_name({'from_name': '', 'from_number': '+12315550140'}),
                         'Fax from (231) 555-0140')
        self.assertEqual(inbound_fax.document_name({'from_name': 'Lab/X: "Main"', 'from_number': ''}),
                         'Fax from Lab X Main')
        self.assertEqual(inbound_fax.document_name({'from_name': '', 'from_number': ''}),
                         'Fax from an unknown number')

    def test_a_dry_run_reads_the_list_and_fetches_nothing(self):
        self.listed = [fax(1), fax(2)]
        summary = inbound_fax.import_new_faxes(dry_run=True)
        self.assertEqual((summary['would_import'], summary['imported']), (2, 0))
        self.assertEqual(self.downloads, [])
        self.assertFalse(InboundFax.objects.exists())

    # The job command

    def test_the_command_prints_one_summary_line(self):
        self.listed = [fax(1)]
        out = io.StringIO()
        call_command('import_inbound_faxes', '--dry-run', stdout=out)
        row = json.loads(out.getvalue())
        self.assertEqual((row['kind'], row['ok'], row['dry_run'], row['would_import']),
                         ('inbound_fax_import', True, True, 1))

    def test_the_command_fails_when_ringcentral_cannot_be_read(self):
        def refuse(days=7, trace=None):
            raise rc.FaxError('RingCentral could not be reached: timed out')
        out = io.StringIO()
        with mock.patch.object(rc, 'inbound_faxes', refuse), self.assertRaises(CommandError):
            call_command('import_inbound_faxes', stdout=out)
        self.assertFalse(json.loads(out.getvalue())['ok'])


class RemoveStoredFaxesFromRingCentralTests(_InboundFaxBase):
    """Once a fax is stored here, the scheduled job moves it to RingCentral's
    Deleted folder (owner, 2026-11-18: "ok to delete documents from ring
    central once we have downloaded"). Deleted, never purged; only the job;
    only with the EditMessages permission."""

    def setUp(self):
        super().setUp()
        self.granted = {'ReadMessages', 'Faxes', 'EditMessages'}

    def job(self, **kwargs):
        kwargs.setdefault('delete_batch', inbound_fax.DELETE_PER_RUN)
        return inbound_fax.import_new_faxes(batch=kwargs.pop('batch', 25), trigger='job', **kwargs)

    def test_the_job_stores_each_fax_then_deletes_it_from_ringcentral(self):
        self.listed = [fax(1), fax(2)]
        summary = self.job()
        self.assertEqual(summary['imported'], 2)
        self.assertEqual(self.rc_deleted, ['1', '2'])
        self.assertEqual((summary['rc_delete'], summary['rc_deleted'], summary['rc_waiting']), ('done', 2, 0))
        self.assertEqual(Document.objects.filter(team=self.team, patient=None).count(), 2, 'the stored copies stay')

    def test_a_mac_check_never_deletes(self):
        self.listed = [fax(1)]
        summary = inbound_fax.import_new_faxes(trigger='app')
        self.assertEqual(summary['imported'], 1)
        self.assertEqual(self.rc_deleted, [])
        self.assertEqual(summary['rc_delete'], 'not_this_pass')

    def test_a_fax_not_stored_here_stays_in_ringcentral(self):
        self.failures['2'] = rc.FaxError('boom', 500)
        self.listed = [fax(1), fax(2), fax(3, received='2026-11-15T09:00:00Z'), fax(4, attachments=[])]
        self.job()
        self.assertEqual(self.rc_deleted, ['1'], 'failed, before the start and given up all stay')

    def test_only_a_live_fax_is_deleted_so_none_is_ever_purged(self):
        self.listed = [fax(1)]
        self.job(delete_batch=0)
        self.listed = [fax(1, availability='Deleted'), fax(5, availability='Purged')]
        summary = self.job()
        self.assertEqual(self.rc_deleted, [], 'a second DELETE would purge it')
        self.assertEqual(summary['rc_delete'], 'nothing_to_delete')

    def test_a_record_with_no_availability_is_left_alone(self):
        self.listed = [fax(1, availability='')]
        self.job()
        self.assertEqual(self.rc_deleted, [])

    def test_a_fax_deleted_here_still_leaves_ringcentral(self):
        self.listed = [fax(1)]
        self.job(delete_batch=0)
        Document.objects.filter(team=self.team).delete()
        summary = self.job()
        self.assertEqual(self.rc_deleted, ['1'])
        self.assertEqual(summary['deleted'], 1)

    def test_without_the_permission_nothing_is_sent(self):
        self.granted = {'ReadMessages', 'Faxes', 'ReadContacts'}
        self.listed = [fax(1), fax(2)]
        summary = self.job()
        self.assertEqual(self.rc_deleted, [])
        self.assertEqual((summary['rc_delete'], summary['rc_waiting']), ('no_permission', 2))

    def test_an_unknown_scope_tries_and_a_refusal_stops_the_run(self):
        self.granted = None
        self.listed = [fax(1), fax(2)]
        self.delete_failures['1'] = rc.FaxError('needs EditMessages', 403)
        summary = self.job()
        self.assertEqual(self.rc_deleted, ['1'])
        self.assertEqual((summary['rc_delete'], summary['rc_deleted'], summary['rc_waiting']), ('not_allowed', 0, 2))

    def test_a_message_already_gone_is_not_a_failure(self):
        self.listed = [fax(1), fax(2)]
        self.delete_failures['1'] = rc.FaxError('not found', 404)
        summary = self.job()
        self.assertEqual(self.rc_deleted, ['1', '2'])
        self.assertEqual((summary['rc_delete'], summary['rc_deleted'], summary['rc_waiting']), ('done', 1, 0))

    def test_switched_off_deletes_nothing(self):
        self.listed = [fax(1)]
        with override_settings(INBOUND_FAX_DELETE_IMPORTED=False):
            summary = self.job()
        self.assertEqual(self.rc_deleted, [])
        self.assertEqual(summary['rc_delete'], 'off')

    def test_each_run_deletes_at_most_its_share_oldest_first(self):
        self.listed = [fax(3, received='2026-11-16T15:00:00Z'), fax(1), fax(2, received='2026-11-16T14:00:00Z')]
        summary = self.job(delete_batch=2)
        self.assertEqual(self.rc_deleted, ['1', '2'])
        self.assertEqual(summary['rc_waiting'], 1)

    def test_a_rate_limited_import_deletes_nothing(self):
        self.failures['1'] = rc.FaxError('slow down', 429)
        self.listed = [fax(1)]
        summary = self.job()
        self.assertEqual(self.rc_deleted, [])
        self.assertEqual(summary['rc_delete'], 'rate_limited')

    def test_a_dry_run_only_counts(self):
        self.listed = [fax(1)]
        self.job(delete_batch=0)
        summary = self.job(dry_run=True)
        self.assertEqual(self.rc_deleted, [])
        self.assertEqual((summary['rc_delete'], summary['would_delete_from_ringcentral']), ('dry_run', 1))

    def test_the_command_deletes_by_default_and_can_skip_it(self):
        self.listed = [fax(1)]
        out = io.StringIO()
        call_command('import_inbound_faxes', '--delete-batch', '0', stdout=out)
        self.assertEqual(json.loads(out.getvalue())['rc_delete'], 'not_this_pass')
        self.assertEqual(self.rc_deleted, [])
        out = io.StringIO()
        call_command('import_inbound_faxes', stdout=out)
        self.assertEqual(json.loads(out.getvalue())['rc_deleted'], 1)
        self.assertEqual(self.rc_deleted, ['1'])
