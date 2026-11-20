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


class MoveFaxToDeletedTests(SimpleTestCase):
    """Deleting a received fax from RingCentral (owner, 2026-11-18): one
    DELETE, never a purge, and the app's permissions read off the token."""

    setUp = RingCentralFaxTests.setUp
    _http = RingCentralFaxTests._http
    TOKEN = RingCentralFaxTests.TOKEN

    def test_it_is_one_delete_of_that_message_and_never_a_purge(self):
        self.answers = [self.TOKEN, (204, {})]
        rc.move_fax_to_deleted('3903777950022')
        method, url, headers, body = self.calls[1]
        self.assertEqual(method, 'DELETE')
        self.assertTrue(url.endswith('/restapi/v1.0/account/~/extension/~/message-store/3903777950022'), url)
        self.assertNotIn('purge', url)
        self.assertIsNone(body)
        self.assertEqual(headers['Authorization'], 'Bearer tok')

    def test_a_refusal_raises_with_its_status(self):
        self.answers = [self.TOKEN, (403, {'message': 'In order to call this API endpoint, application needs to have [EditMessages] permission'})]
        with self.assertRaises(rc.FaxError) as caught:
            rc.move_fax_to_deleted('7')
        self.assertEqual(caught.exception.status, 403)
        self.assertIn('EditMessages', str(caught.exception))

    def test_the_permissions_come_from_the_token(self):
        self.answers = [(200, {'access_token': 'tok', 'expires_in': 7199,
                               'scope': 'ReadMessages Faxes ReadContacts EditMessages'})]
        self.assertEqual(rc.granted_permissions(), {'ReadMessages', 'Faxes', 'ReadContacts', 'EditMessages'})
        self.assertEqual(len(self.calls), 1, 'one sign-in, reused')
        self.assertIn('EditMessages', rc.granted_permissions())

    def test_a_token_without_a_scope_says_unknown_not_nothing(self):
        self.answers = [self.TOKEN]
        self.assertIsNone(rc.granted_permissions())


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


class InboundFaxListTests(SimpleTestCase):
    """`inbound_faxes` reads the received-fax list and nothing else, and the
    pager under it reads to the end of a list."""

    setUp = RingCentralFaxTests.setUp
    _http = RingCentralFaxTests._http
    TOKEN = RingCentralFaxTests.TOKEN

    def _page(self, ids, **paging):
        return (200, {'records': [{'id': i, 'creationTime': '2026-11-%02dT10:00:00Z' % (10 + i)} for i in ids],
                      'paging': paging})

    def test_it_asks_for_inbound_faxes_since_the_window_and_reads_each_record(self):
        self.answers = [self.TOKEN, (200, {'records': [{
            'id': 11, 'creationTime': '2026-11-16T13:42:00Z', 'faxPageCount': 3,
            'readStatus': 'Unread', 'messageStatus': 'Received', 'availability': 'Alive',
            'from': {'phoneNumber': '+12315550140', 'name': 'NMRL'},
            'to': [{'phoneNumber': '+12315388295', 'name': ''}],
            'attachments': [{'contentType': 'application/pdf', 'size': 81234}],
        }], 'paging': {'totalPages': 1}})]
        trace = {}
        faxes = rc.inbound_faxes(days=7, trace=trace)
        method, url, _, body = self.calls[1]
        self.assertEqual(method, 'GET')
        self.assertIn('/message-store?', url)
        self.assertIn('direction=Inbound', url)
        self.assertIn('messageType=Fax', url)
        self.assertIn('dateFrom=', url)
        self.assertIsNone(body)
        self.assertEqual(faxes, [{
            'id': 11, 'received': '2026-11-16T13:42:00Z', 'from_number': '+12315550140',
            'from_name': 'NMRL', 'to_numbers': ['+12315388295'], 'to_keys': ['phoneNumber'], 'pages': 3,
            'read_status': 'Unread', 'message_status': 'Received', 'availability': 'Alive',
            'attachments': [{'id': None, 'content_type': 'application/pdf', 'size': 81234}]}])
        self.assertTrue(trace['complete'])
        self.assertEqual(trace['stopped'], 'last_page')

    def test_odd_records_do_not_break_the_list(self):
        self.answers = [self.TOKEN, (200, {'records': [{'id': 1, 'from': 'x', 'attachments': ['y'],
                                                        'faxPageCount': 'two'}],
                                           'paging': {'totalPages': 1}})]
        fax = rc.inbound_faxes()[0]
        self.assertEqual((fax['from_number'], fax['pages'], fax['attachments'], fax['to_keys']),
                         ('', None, [], []))

    def test_a_refused_list_raises(self):
        self.answers = [self.TOKEN, (403, {'message': 'needs [ReadMessages] permission'})]
        with self.assertRaises(rc.FaxError):
            rc.inbound_faxes()

    def test_a_missing_page_total_does_not_end_the_read_early(self):
        """RingCentral can leave `totalPages` out; a full page means read on."""
        self.answers = [self.TOKEN, self._page([1, 2], perPage=2), self._page([3], perPage=2)]
        trace = {}
        records = rc._paged_through('/x', {'perPage': 2}, 10, trace)
        self.assertEqual([r['id'] for r in records], [1, 2, 3])
        self.assertEqual((trace['stopped'], trace['complete'], trace['pages']), ('short_page', True, 2))
        self.assertEqual((trace['oldest'], trace['newest']), ('2026-11-11', '2026-11-13'))
        self.assertIn('page=2', self.calls[2][1])

    def test_a_next_page_link_is_followed_even_after_a_short_page(self):
        self.answers = [self.TOKEN, (200, {'records': [{'id': 1}], 'paging': {'perPage': 2},
                                           'navigation': {'nextPage': {'uri': 'x'}}}),
                        (200, {'records': [], 'paging': {'perPage': 2}})]
        trace = {}
        self.assertEqual(len(rc._paged_through('/x', {'perPage': 2}, 10, trace)), 1)
        self.assertEqual((trace['stopped'], trace['complete']), ('empty_page', True))
        self.assertEqual(trace['navigation_keys'], ['nextPage'])

    def test_running_out_of_pages_is_reported_as_incomplete(self):
        self.answers = [self.TOKEN, self._page([1, 2], perPage=2), self._page([3, 4], perPage=2)]
        trace = {}
        self.assertEqual(len(rc._paged_through('/x', {'perPage': 2}, 2, trace)), 4)
        self.assertEqual((trace['stopped'], trace['complete']), ('max_pages', False))

    def test_the_import_pager_still_stops_without_a_total_and_says_so(self):
        """`_paged` (what the directory import uses) is unchanged; the trace names why it stopped."""
        self.answers = [self.TOKEN, self._page([1, 2], perPage=2)]
        trace = {}
        self.assertEqual(len(rc._paged('/x', {'perPage': 2}, 5, trace)), 2)
        self.assertEqual((trace['stopped'], trace['pages'], trace['records']), ('no_total_pages', 1, 2))

    def test_the_extension_numbers_are_read_when_allowed(self):
        self.answers = [self.TOKEN, (200, {'records': [{'phoneNumber': '+12315388295', 'usageType': 'DirectNumber',
                                                        'type': 'VoiceFax', 'features': ['FaxNumber', 'CallerId']}]})]
        self.assertEqual(rc.extension_phone_numbers(), [{
            'phone_number': '+12315388295', 'usage_type': 'DirectNumber', 'type': 'VoiceFax',
            'features': ['CallerId', 'FaxNumber']}])


class CheckRingCentralInboundCommandTests(SimpleTestCase):
    """`manage.py check_ringcentral_inbound` prints counts, dates and the last
    four digits of the practice's own numbers; never a name or a full number."""

    FAXES = [
        {'id': 1, 'received': '2026-11-16T13:42:00Z', 'from_number': '+12315550140', 'from_name': 'NMRL',
         'to_numbers': ['+12315388295'], 'to_keys': ['name', 'phoneNumber'], 'pages': 3, 'read_status': 'Read',
         'message_status': 'Received', 'attachments': [{'content_type': 'application/pdf', 'size': None}]},
        {'id': 2, 'received': '2026-11-16T14:00:00Z', 'from_number': '+12315550140', 'from_name': '',
         'to_numbers': ['+12315388295'], 'to_keys': ['phoneNumber'], 'pages': 1, 'read_status': 'Unread',
         'message_status': 'Received', 'attachments': [{'content_type': 'application/pdf', 'size': 5000}]},
        {'id': 3, 'received': '2026-11-15T09:00:00Z', 'from_number': '', 'from_name': 'Anonymous',
         'to_numbers': [''], 'to_keys': ['name'], 'pages': None, 'read_status': 'Unread',
         'message_status': 'Received', 'attachments': []},
    ]
    SENT = [
        {'id': 9, 'creationTime': '2099-01-01T10:00:00Z', 'to': [{'phoneNumber': '+12315388253', 'name': 'James'}]},
        {'id': 8, 'creationTime': '2026-01-05T10:00:00Z', 'to': [{'phoneNumber': '(231) 538-8253'}]},
        {'id': 7, 'creationTime': '2026-01-04T10:00:00Z', 'to': [{'phoneNumber': '+12315550140'}]},
    ]

    def _run(self, faxes=None, inbound_error=None, contacts_error=None, configured=True):
        import io
        import json
        from django.core.management import call_command
        from django.core.management.base import CommandError

        def read_inbound(days=7, trace=None):
            if inbound_error:
                raise rc.FaxError(inbound_error)
            if trace is not None:
                trace.update(pages=1, stopped='last_page', complete=True)
            return faxes or []

        def read_outbound(days=365, trace=None, max_pages=20):
            if trace is not None:
                trace.update(records=3, oldest='2026-01-04', newest='2099-01-01', complete=True)
            return self.SENT

        def read_import(days=365, trace=None):
            if trace is not None:
                trace.update(records=3, stopped='no_total_pages', oldest='2026-01-04')
            return []

        def read_contacts():
            if contacts_error:
                raise rc.FaxError(contacts_error)
            return [{'fax_number': '231-555-0140', 'name': 'NMRL', 'note': ''}]

        def read_own_numbers():
            raise rc.FaxError('needs [ReadAccounts] permission')

        out = io.StringIO()
        error = None
        with mock.patch.object(rc, 'is_configured', lambda: configured), \
                mock.patch.object(rc, '_access_token', lambda force=False: 'tok'), \
                mock.patch.object(rc, 'inbound_faxes', read_inbound), \
                mock.patch.object(rc, 'outbound_fax_records', read_outbound), \
                mock.patch.object(rc, 'sent_fax_numbers', read_import), \
                mock.patch.object(rc, 'contact_fax_numbers', read_contacts), \
                mock.patch.object(rc, 'extension_phone_numbers', read_own_numbers), \
                mock.patch('emr.management.commands.check_ringcentral_inbound.FaxRecipient') as recipients:
            recipients.objects.filter.return_value.values_list.return_value = ['12315550140', '17345550000']
            try:
                call_command('check_ringcentral_inbound', stdout=out)
            except CommandError as raised:
                error = raised
        text = out.getvalue()
        return {row['kind']: row for row in map(json.loads, text.splitlines())}, text, error

    def test_it_reports_counts_and_no_names_or_full_numbers(self):
        rows, text, error = self._run(self.FAXES)
        self.assertIsNone(error)
        self.assertEqual(rows['inbound']['faxes'], 3)
        self.assertTrue(rows['inbound']['complete'])
        self.assertEqual(rows['inbound']['to_clinic_line'], 2)
        self.assertEqual((rows['inbound']['read'], rows['inbound']['unread']), (1, 2))
        self.assertEqual(rows['receiving_numbers']['by_last_four'], {'8295': 2})
        self.assertEqual(rows['receiving_numbers']['faxes_with_no_to_number'], 1)
        self.assertEqual(rows['receiving_numbers']['to_fields_seen'], {'name': 2, 'phoneNumber': 2})
        self.assertEqual(rows['by_day']['days'], {'2026-11-15': 1, '2026-11-16': 2})
        self.assertEqual((rows['pages']['total'], rows['pages']['largest'], rows['pages']['unknown']), (4, 3, 1))
        self.assertEqual((rows['attachments']['with_pdf'], rows['attachments']['with_none'],
                          rows['attachments']['sizes_reported']), (2, 1, 1))
        self.assertEqual(rows['senders'], {
            'kind': 'senders', 'distinct': 1, 'no_number': 1, 'with_sender_name': 2,
            'directory_entries': 2, 'in_directory': 1, 'faxes_from_directory_numbers': 2,
            'faxed_by_clinic_in_history': 1, 'faxes_from_numbers_faxed_by_clinic': 2,
            'in_contacts': 1, 'contacts_reason': None})
        self.assertEqual((rows['refaxed_to_physician']['in_window'], rows['refaxed_to_physician']['in_history']), (1, 2))
        self.assertEqual(rows['history_reach']['as_the_import_reads_it']['stopped'], 'no_total_pages')
        self.assertTrue(rows['history_reach']['read_to_the_end']['complete'])
        self.assertTrue(rows['summary']['ok'])
        for secret in ('NMRL', 'Anonymous', 'James', '5550140', '5388253', '5388295', '5550000'):
            self.assertNotIn(secret, text)

    def test_the_optional_reads_failing_does_not_fail_the_check(self):
        rows, _, error = self._run(self.FAXES, contacts_error='needs [ReadContacts] permission')
        self.assertIsNone(error)
        self.assertFalse(rows['extension_numbers']['ok'])
        self.assertIn('ReadAccounts', rows['extension_numbers']['reason'])
        self.assertIsNone(rows['senders']['in_contacts'])
        self.assertIn('ReadContacts', rows['senders']['contacts_reason'])
        self.assertTrue(rows['summary']['ok'])

    def test_a_refused_inbound_list_is_named_and_fails_the_command(self):
        rows, _, error = self._run(inbound_error='needs [ReadMessages] permission')
        self.assertIsNotNone(error)
        self.assertFalse(rows['inbound']['ok'])
        self.assertIn('ReadMessages', rows['inbound']['reason'])
        self.assertFalse(rows['summary']['ok'])

    def test_an_empty_mailbox_is_reported_as_zero_not_an_error(self):
        rows, _, error = self._run([])
        self.assertIsNone(error)
        self.assertEqual(rows['inbound']['faxes'], 0)
        self.assertIsNone(rows['pages']['largest'])

    def test_an_unconfigured_server_stops_at_once(self):
        rows, _, error = self._run(configured=False)
        self.assertIsNotNone(error)
        self.assertEqual(set(rows), {'config', 'summary'})


class FaxAttachmentTests(SimpleTestCase):
    """`fax_attachment` downloads one received fax's PDF with the clinic's token."""

    setUp = RingCentralFaxTests.setUp
    _http = RingCentralFaxTests._http
    TOKEN = RingCentralFaxTests.TOKEN

    def _with_bytes(self, *answers):
        self.byte_calls = []
        queue = list(answers)

        def fake(url, headers):
            self.byte_calls.append((url, headers))
            return queue.pop(0)
        patcher = mock.patch.object(rc, '_http_bytes', fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_it_asks_for_the_attachment_on_the_configured_server_with_the_token(self):
        self.answers = [self.TOKEN]
        self._with_bytes((200, b'%PDF-1.4 x', 'application/pdf; charset=binary', {}))
        data, content_type = rc.fax_attachment(11, 901)
        self.assertEqual((data, content_type), (b'%PDF-1.4 x', 'application/pdf'))
        url, headers = self.byte_calls[0]
        self.assertEqual(url, 'https://platform.ringcentral.com/restapi/v1.0/account/~/extension/~/message-store/11/content/901')
        self.assertEqual(headers['Authorization'], 'Bearer tok')

    def test_a_401_gets_one_fresh_token(self):
        self.answers = [self.TOKEN, (200, {'access_token': 'tok2', 'expires_in': 7199})]
        self._with_bytes((401, b'', '', {}), (200, b'%PDF', 'application/pdf', {}))
        self.assertEqual(rc.fax_attachment(1, 2)[0], b'%PDF')
        self.assertEqual(self.byte_calls[1][1]['Authorization'], 'Bearer tok2')

    def test_a_refusal_raises_with_its_status(self):
        self.answers = [self.TOKEN]
        self._with_bytes((429, b'', '', {'message': 'Request rate exceeded'}))
        with self.assertRaises(rc.FaxError) as caught:
            rc.fax_attachment(1, 2)
        self.assertEqual(caught.exception.status, 429)
        self.assertIn('rate exceeded', str(caught.exception))

    def test_odd_ids_never_reach_a_url(self):
        with self.assertRaises(rc.FaxError):
            rc.fax_attachment('1/../2', 3)

    def test_a_file_over_thirty_megabytes_is_refused(self):
        self.answers = [self.TOKEN]
        self._with_bytes((200, b'%PDF' + b'0' * (30 * 1024 * 1024), 'application/pdf', {}))
        with self.assertRaises(rc.FaxError) as caught:
            rc.fax_attachment(1, 2)
        self.assertEqual(caught.exception.status, 413)

    def test_redirects_are_followed_only_to_ringcentral(self):
        for url, allowed in (('https://media.ringcentral.com/x', True),
                             ('https://platform.ringcentral.com/x', True),
                             ('https://ringcentral.com.evil.example/x', False),
                             ('https://example.com/x', False)):
            with self.subTest(url=url):
                self.assertEqual(rc._ringcentral_host(url), allowed)
        handler = rc._RingCentralOnlyRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, 'Found', {}, 'https://example.com/steal'))
