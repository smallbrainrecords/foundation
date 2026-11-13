"""`emr.ringcentral_fax`: what is put on the wire, and how answers are read.
No request leaves the test: `_http` is replaced."""
import os
from unittest import mock

from django.test import SimpleTestCase

from emr import ringcentral_fax as rc

ENV = {
    'RINGCENTRAL_CLIENT_ID': 'cid',
    'RINGCENTRAL_CLIENT_SECRET': 'secret',
    'RINGCENTRAL_JWT': 'the.jwt',
}


class RingCentralFaxTests(SimpleTestCase):

    def setUp(self):
        rc.forget_token()
        self.calls = []
        self.answers = []
        patcher = mock.patch.object(rc, '_http', self._http)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ, ENV)
        env.start()
        self.addCleanup(env.stop)
        self.addCleanup(rc.forget_token)

    def _http(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        return self.answers.pop(0)

    TOKEN = (200, {'access_token': 'tok', 'expires_in': 7199})

    def test_unconfigured_makes_no_request(self):
        with mock.patch.dict(os.environ, {'RINGCENTRAL_JWT': ''}):
            self.assertFalse(rc.is_configured())
            with self.assertRaises(rc.FaxNotConfigured):
                rc.send_fax(b'%PDF', '15865551234')
        self.assertEqual(self.calls, [])

    def test_the_token_request_is_the_jwt_grant_with_basic_credentials(self):
        self.answers = [self.TOKEN, (200, {'id': 7, 'messageStatus': 'Queued'})]
        rc.send_fax(b'%PDF', '15865551234')
        method, url, headers, body = self.calls[0]
        self.assertEqual((method, url), ('POST', 'https://platform.ringcentral.com/restapi/oauth/token'))
        self.assertEqual(headers['Authorization'], 'Basic Y2lkOnNlY3JldA==')
        self.assertIn(b'grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer', body)
        self.assertIn(b'assertion=the.jwt', body)

    def test_the_fax_is_one_pdf_to_one_number_with_no_cover(self):
        self.answers = [self.TOKEN, (200, {'id': 7, 'messageStatus': 'Queued'})]
        sent = rc.send_fax(b'%PDF-bytes', '15865551234')
        self.assertEqual(sent['message_id'], '7')
        self.assertEqual(sent['state'], 'queued')
        method, url, headers, body = self.calls[1]
        self.assertEqual(method, 'POST')
        self.assertTrue(url.endswith('/restapi/v1.0/account/~/extension/~/fax'))
        self.assertEqual(headers['Authorization'], 'Bearer tok')
        self.assertTrue(headers['Content-Type'].startswith('multipart/form-data; boundary='))
        self.assertIn(b'name="to"\r\n\r\n15865551234\r\n', body)
        self.assertIn(b'name="coverIndex"\r\n\r\n0\r\n', body)
        self.assertIn(b'name="attachment"; filename="requisition.pdf"\r\nContent-Type: application/pdf\r\n\r\n%PDF-bytes\r\n', body)
        self.assertEqual(body.count(b'name="to"'), 1)

    def test_one_token_serves_several_requests(self):
        self.answers = [self.TOKEN, (200, {'id': 7}), (200, {'messageStatus': 'Queued'})]
        rc.send_fax(b'%PDF', '15865551234')
        rc.message_status('7')
        self.assertEqual(len([c for c in self.calls if c[1].endswith('/oauth/token')]), 1)

    def test_a_401_gets_one_fresh_token_and_one_more_try(self):
        self.answers = [self.TOKEN, (401, {}), self.TOKEN, (200, {'id': 8})]
        self.assertEqual(rc.send_fax(b'%PDF', '15865551234')['message_id'], '8')

    def test_a_refusal_raises_with_ringcentrals_words(self):
        self.answers = [self.TOKEN, (400, {'message': 'Parameter [to] value is invalid'})]
        with self.assertRaises(rc.FaxError) as caught:
            rc.send_fax(b'%PDF', '15865551234')
        self.assertIn('Parameter [to] value is invalid', str(caught.exception))

    def test_a_failed_sign_in_raises(self):
        self.answers = [(400, {'error_description': 'Invalid JWT'})]
        with self.assertRaises(rc.FaxError) as caught:
            rc.message_status('7')
        self.assertIn('Invalid JWT', str(caught.exception))

    def test_statuses_are_read_into_three_states(self):
        for status, state in (('Queued', 'queued'), ('Sent', 'delivered'), ('Delivered', 'delivered'),
                              ('SendingFailed', 'failed'), ('DeliveryFailed', 'failed'),
                              ('SomethingNew', 'queued'), ('', 'queued')):
            self.assertEqual(rc._state_for(status), state, status)

    def test_a_recipient_level_failure_wins_and_carries_its_reason(self):
        self.answers = [self.TOKEN, (200, {
            'messageStatus': 'Sent', 'faxPageCount': 2,
            'to': [{'messageStatus': 'SendingFailed', 'faxErrorCode': 'Busy'}]})]
        reading = rc.message_status('7')
        self.assertEqual(reading['state'], 'failed')
        self.assertEqual(reading['error'], 'Busy')
        self.assertEqual(reading['page_count'], 2)

    # ---- reading contacts and sent faxes ----

    def test_contacts_give_one_entry_per_fax_number_named_for_the_place(self):
        self.answers = [self.TOKEN, (200, {'paging': {'totalPages': 1}, 'records': [
            {'firstName': 'Pat', 'lastName': 'Smith', 'company': 'Quest Diagnostics',
             'businessFax': '+15865551234', 'otherFax': '(586) 555-9999', 'businessPhone': '+15865550000'},
            {'firstName': 'Dana', 'lastName': 'Lee', 'businessFax': '2485557777'},
            {'firstName': 'No', 'lastName': 'Fax', 'mobilePhone': '+15865550001'},
        ]})]
        found = rc.contact_fax_numbers()
        self.assertEqual(found, [
            {'fax_number': '+15865551234', 'name': 'Quest Diagnostics', 'note': 'Pat Smith'},
            {'fax_number': '(586) 555-9999', 'name': 'Quest Diagnostics', 'note': 'Pat Smith'},
            {'fax_number': '2485557777', 'name': 'Dana Lee', 'note': ''},
        ])
        url = self.calls[1][1]
        self.assertIn('/restapi/v1.0/account/~/extension/~/address-book/contact?', url)
        self.assertIn('perPage=1000', url)

    def test_contact_pages_are_followed_but_capped(self):
        page = (200, {'paging': {'totalPages': 99}, 'records': [{'company': 'A', 'businessFax': '5865551234'}]})
        self.answers = [self.TOKEN] + [page] * 10
        found = rc.contact_fax_numbers()
        self.assertEqual(len(found), rc._CONTACT_MAX_PAGES)
        self.assertEqual(len(self.calls), 1 + rc._CONTACT_MAX_PAGES)

    def test_a_refused_contact_read_raises(self):
        self.answers = [self.TOKEN, (403, {'message': 'In order to call this API endpoint, application needs to have [ReadContacts] permission'})]
        with self.assertRaises(rc.FaxError) as caught:
            rc.contact_fax_numbers()
        self.assertIn('ReadContacts', str(caught.exception))

    def test_sent_faxes_are_counted_per_number_with_deliveries_apart(self):
        self.answers = [self.TOKEN, (200, {'paging': {'totalPages': 1}, 'records': [
            {'creationTime': '2026-11-01T10:00:00Z', 'messageStatus': 'Sent',
             'to': [{'phoneNumber': '+15865551234', 'messageStatus': 'Sent', 'name': 'Quest'}]},
            {'creationTime': '2026-10-01T10:00:00Z', 'messageStatus': 'SendingFailed',
             'to': [{'phoneNumber': '+15865551234', 'messageStatus': 'SendingFailed', 'faxErrorCode': 'LineBusy'}]},
            {'creationTime': '2026-09-01T10:00:00Z', 'messageStatus': 'Sent',
             'to': [{'phoneNumber': '+12485557777'}, {'phoneNumber': ''}]},
        ]})]
        found = {e['fax_number']: e for e in rc.sent_fax_numbers()}
        self.assertEqual(found['+15865551234'], {
            'fax_number': '+15865551234', 'name': 'Quest', 'times_faxed': 2,
            'times_delivered': 1, 'last_faxed': '2026-11-01T10:00:00Z'})
        # No per-recipient status: the message's own decides.
        self.assertEqual(found['+12485557777']['times_delivered'], 1)
        url = self.calls[1][1]
        self.assertIn('messageType=Fax', url)
        self.assertIn('direction=Outbound', url)
        # Without dateFrom RingCentral answers for the last 24 hours only.
        self.assertIn('dateFrom=', url)


class CheckRingCentralFaxCommandTests(SimpleTestCase):
    """`manage.py check_ringcentral_fax` prints counts and never a name or
    a number. (The directory count is patched: no database here.)"""

    def _run(self, contacts=None, history=None, contacts_error=None, configured=True):
        import io
        import json
        from django.core.management import call_command
        from django.core.management.base import CommandError

        def read_contacts():
            if contacts_error:
                raise rc.FaxError(contacts_error)
            return contacts or []

        out = io.StringIO()
        error = None
        with mock.patch.object(rc, 'is_configured', lambda: configured), \
                mock.patch.object(rc, '_access_token', lambda force=False: 'tok'), \
                mock.patch.object(rc, 'contact_fax_numbers', read_contacts), \
                mock.patch.object(rc, 'sent_fax_numbers', lambda days=365: history or []), \
                mock.patch('emr.management.commands.check_ringcentral_fax.FaxRecipient') as recipients:
            recipients.objects.filter.return_value.values_list.return_value = ['15865551234']
            try:
                call_command('check_ringcentral_fax', stdout=out)
            except CommandError as raised:
                error = raised
        text = out.getvalue()
        return {row['kind']: row for row in map(json.loads, text.splitlines())}, text, error

    CONTACTS = [{'fax_number': '(586) 555-1234', 'name': 'Quest Diagnostics', 'note': 'Pat Smith'},
                {'fax_number': '555', 'name': '', 'note': ''}]
    HISTORY = [{'fax_number': '+12485557777', 'name': 'Henry Ford', 'times_faxed': 4,
                'times_delivered': 3, 'last_faxed': '2026-11-01T10:00:00Z'}]

    def test_it_reports_counts_and_no_names_or_numbers(self):
        rows, text, error = self._run(self.CONTACTS, self.HISTORY)
        self.assertIsNone(error)
        self.assertEqual(rows['contacts']['fax_numbers'], 2)
        self.assertEqual(rows['contacts']['valid_numbers'], 1)
        self.assertEqual((rows['history']['faxes'], rows['history']['delivered']), (4, 3))
        self.assertEqual(rows['history']['newest'], '2026-11-01')
        self.assertEqual(rows['import'], {
            'kind': 'import', 'distinct_numbers': 2, 'already_in_directory': 1, 'would_offer': 1})
        self.assertTrue(rows['summary']['ok'])
        for secret in ('Quest', 'Pat Smith', 'Henry Ford', '5865551234', '2485557777'):
            self.assertNotIn(secret, text)

    def test_a_failed_read_is_named_and_fails_the_command(self):
        rows, _, error = self._run(history=self.HISTORY, contacts_error='needs [ReadContacts] permission')
        self.assertIsNotNone(error)
        self.assertFalse(rows['contacts']['ok'])
        self.assertIn('ReadContacts', rows['contacts']['reason'])
        self.assertTrue(rows['history']['ok'])
        self.assertFalse(rows['summary']['ok'])

    def test_an_unconfigured_server_stops_at_once(self):
        rows, _, error = self._run(configured=False)
        self.assertIsNotNone(error)
        self.assertEqual(set(rows), {'config', 'summary'})
