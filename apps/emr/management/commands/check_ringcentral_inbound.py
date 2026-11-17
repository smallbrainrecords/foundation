"""`check_ringcentral_inbound` — do the clinic's incoming faxes land in the
mailbox this server's RingCentral credential can read, and how many are there?

Written 2026-11-16 as step 0 of the inbound-fax plan (SBR1
PLAN_INBOUND_FAX_2026-11.md). It reads only: it signs in and lists the
credential owner's received and sent faxes (and, if allowed, the owner's own
phone numbers and contacts). It never downloads a page, never marks a fax
read, never sends anything.

Output is one JSON object per line on stdout:

  * `kind: "config"`   — whether the three RINGCENTRAL_* values are set.
  * `kind: "sign_in"`  — whether RingCentral issued a token.
  * `kind: "inbound"`  — received faxes in the window: how many, how many were
    addressed to the clinic line, read / unread, message statuses, the oldest
    and newest day, and whether the list was read to its end.
  * `kind: "inbound_paging"` — how the received-fax list was paged.
  * `kind: "receiving_numbers"` — which numbers the faxes were addressed to,
    as the LAST FOUR DIGITS only (they are the practice's own numbers), how
    many faxes had no number in `to`, and which `to` fields RingCentral filled.
  * `kind: "extension_numbers"` — the credential owner's own numbers (last
    four digits, usage type, features). Needs the ReadAccounts permission;
    a refusal is reported and does not fail the check.
  * `kind: "by_day"`   — faxes per calendar day (UTC), and per weekday.
  * `kind: "pages"`    — total, median, 90th percentile and largest page
    count, and how many faxes had no page count.
  * `kind: "attachments"` — faxes with a PDF attachment, with none, with
    another type, and how many attachments reported a size.
  * `kind: "senders"`  — distinct sending numbers; how many arrived with no
    number or a sender name; active fax-directory entries; how many senders
    are in the directory, were faxed by this extension within the history
    read, or are in the owner's contacts (optional read).
  * `kind: "history_reach"` — how far back the 365-day sent-fax history
    really reaches, read two ways: as the fax-directory import reads it
    (`sent_fax_numbers`, which stops when RingCentral leaves out the page
    total) and read to the end of the list.
  * `kind: "refaxed_to_physician"` — faxes this extension sent to the
    physician's line in the window and over the whole history read (the
    forwarding step the plan removes). Faxes forwarded from staff members'
    own RingCentral users are not visible here, so these are lower bounds.
  * `kind: "summary"`  — `ok` is true when the required reads worked (sign-in,
    received faxes, sent faxes), last.

Counts, dates and last-four digits of the practice's own numbers only: no
names, no full numbers, no patient data. Run it as a Cloud Run job with the
RINGCENTRAL_* secrets attached:

    manage.py check_ringcentral_inbound [--days 7] [--physician-line 2315388253]
"""
import collections
import datetime
import json
import statistics

from django.core.management.base import BaseCommand, CommandError

from emr import ringcentral_fax
from emr.models import FaxRecipient

CLINIC_LINE = '12315388295'
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _digits(number):
    d = ''.join(ch for ch in (number or '') if ch.isdigit())
    if len(d) == 10:
        d = '1' + d
    return d


def _recipients(record):
    return {_digits(party.get('phoneNumber')) for party in record.get('to') or []
            if isinstance(party, dict) and party.get('phoneNumber')}


class Command(BaseCommand):
    help = "Read-only count of the faxes the RingCentral credential's extension received."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7)
        parser.add_argument('--physician-line', default='2315388253')

    def _emit(self, **row):
        self.stdout.write(json.dumps(row))

    def handle(self, *args, **options):
        days = max(1, options['days'])
        physician_line = _digits(options['physician_line'])

        configured = ringcentral_fax.is_configured()
        self._emit(kind='config', configured=configured)
        if not configured:
            self._emit(kind='summary', ok=False)
            raise CommandError('The RINGCENTRAL_* values are not all set.')
        try:
            ringcentral_fax.forget_token()
            ringcentral_fax._access_token()
            self._emit(kind='sign_in', ok=True)
        except ringcentral_fax.FaxError as error:
            self._emit(kind='sign_in', ok=False, reason=str(error)[:300])
            self._emit(kind='summary', ok=False)
            raise CommandError('RingCentral sign-in failed.')

        ok = True

        # The sent-fax history first: the senders row compares against it.
        sent_records = None
        full_trace, import_trace = {}, {}
        try:
            sent_records = ringcentral_fax.outbound_fax_records(days=ringcentral_fax.HISTORY_DAYS, trace=full_trace)
            ringcentral_fax.sent_fax_numbers(days=ringcentral_fax.HISTORY_DAYS, trace=import_trace)
            self._emit(kind='history_reach', ok=True, asked_days=ringcentral_fax.HISTORY_DAYS,
                       as_the_import_reads_it=import_trace, read_to_the_end=full_trace)
        except ringcentral_fax.FaxError as error:
            ok = False
            self._emit(kind='history_reach', ok=False, reason=str(error)[:300])

        if sent_records is not None:
            since = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%SZ')
            to_physician = [r for r in sent_records if physician_line in _recipients(r)]
            self._emit(
                kind='refaxed_to_physician', ok=True, days=days,
                in_window=sum(1 for r in to_physician if (r.get('creationTime') or '') >= since),
                in_history=len(to_physician), history_from=full_trace.get('oldest', ''),
                note='from this extension only; lower bounds')

        inbound_trace = {}
        try:
            faxes = ringcentral_fax.inbound_faxes(days=days, trace=inbound_trace)
        except ringcentral_fax.FaxError as error:
            self._emit(kind='inbound', ok=False, days=days, reason=str(error)[:300])
            faxes = None
            ok = False

        if faxes is not None:
            days_seen = sorted(f['received'][:10] for f in faxes if f['received'])
            self._emit(
                kind='inbound', ok=True, days=days, faxes=len(faxes),
                complete=inbound_trace.get('complete'),
                to_clinic_line=sum(1 for f in faxes if CLINIC_LINE in {_digits(n) for n in f['to_numbers']}),
                read=sum(1 for f in faxes if f['read_status'] == 'Read'),
                unread=sum(1 for f in faxes if f['read_status'] == 'Unread'),
                statuses=dict(collections.Counter(f['message_status'] or 'none' for f in faxes)),
                oldest=days_seen[0] if days_seen else '', newest=days_seen[-1] if days_seen else '')
            self._emit(kind='inbound_paging', **inbound_trace)

            receiving = collections.Counter()
            fields = collections.Counter()
            no_number = 0
            for f in faxes:
                numbers = {_digits(n) for n in f['to_numbers'] if _digits(n)}
                if not numbers:
                    no_number += 1
                for n in numbers:
                    receiving[n[-4:]] += 1
                for key in f.get('to_keys') or []:
                    fields[key] += 1
            self._emit(kind='receiving_numbers', by_last_four=dict(receiving.most_common(5)),
                       other_numbers=max(0, len(receiving) - 5), faxes_with_no_to_number=no_number,
                       to_fields_seen=dict(fields))

            per_day = collections.Counter(days_seen)
            per_weekday = collections.Counter()
            for day in days_seen:
                try:
                    per_weekday[WEEKDAYS[datetime.date.fromisoformat(day).weekday()]] += 1
                except ValueError:
                    pass
            self._emit(kind='by_day', days=dict(sorted(per_day.items())),
                       weekdays={w: per_weekday.get(w, 0) for w in WEEKDAYS})

            counts = sorted(f['pages'] for f in faxes if f['pages'] is not None)
            self._emit(
                kind='pages', total=sum(counts),
                median=statistics.median(counts) if counts else None,
                p90=counts[int(0.9 * (len(counts) - 1))] if counts else None,
                largest=counts[-1] if counts else None,
                unknown=sum(1 for f in faxes if f['pages'] is None))

            self._emit(
                kind='attachments',
                with_pdf=sum(1 for f in faxes if any('pdf' in a['content_type'].lower() for a in f['attachments'])),
                with_none=sum(1 for f in faxes if not f['attachments']),
                other_types=sorted({a['content_type'] for f in faxes for a in f['attachments']
                                    if a['content_type'] and 'pdf' not in a['content_type'].lower()}),
                sizes_reported=sum(1 for f in faxes for a in f['attachments'] if a['size'] is not None))

            directory = {_digits(n) for n in
                         FaxRecipient.objects.filter(is_active=True).values_list('fax_number', flat=True)} - {''}
            senders = [_digits(f['from_number']) for f in faxes]
            known = [s for s in senders if s]
            distinct = set(known)
            faxed_by_clinic = set()
            for record in sent_records or []:
                faxed_by_clinic |= _recipients(record)
            contacts, contacts_reason = None, None
            try:
                contacts = {_digits(c['fax_number']) for c in ringcentral_fax.contact_fax_numbers()} - {''}
            except ringcentral_fax.FaxError as error:
                contacts_reason = str(error)[:300]
            self._emit(
                kind='senders', distinct=len(distinct), no_number=len(senders) - len(known),
                with_sender_name=sum(1 for f in faxes if f['from_name']),
                directory_entries=len(directory),
                in_directory=len(distinct & directory),
                faxes_from_directory_numbers=sum(1 for s in known if s in directory),
                faxed_by_clinic_in_history=len(distinct & faxed_by_clinic),
                faxes_from_numbers_faxed_by_clinic=sum(1 for s in known if s in faxed_by_clinic),
                in_contacts=len(distinct & contacts) if contacts is not None else None,
                contacts_reason=contacts_reason)

        try:
            own = ringcentral_fax.extension_phone_numbers()
            self._emit(kind='extension_numbers', ok=True, numbers=[
                {'last_four': _digits(n['phone_number'])[-4:], 'usage_type': n['usage_type'],
                 'type': n['type'], 'features': n['features']} for n in own])
        except ringcentral_fax.FaxError as error:
            self._emit(kind='extension_numbers', ok=False, reason=str(error)[:300],
                       note='optional; needs the ReadAccounts permission')

        self._emit(kind='summary', ok=ok)
        if not ok:
            raise CommandError('A RingCentral read failed.')
