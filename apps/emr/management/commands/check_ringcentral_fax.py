"""`check_ringcentral_fax` — can this server reach RingCentral with its fax
credential, and what would the fax-directory import see?

Written 2026-11-12. Run it (as a Cloud Run job with the three RINGCENTRAL_*
secrets attached) after the credential is first set, after it is replaced,
or when faxing or the import stops working. It reads only: it signs in,
lists the credential owner's contacts and the past year's sent faxes, and
never sends a fax.

Output is one JSON object per line on stdout:

  * `kind: "config"`   — whether the three values are set.
  * `kind: "sign_in"`  — whether RingCentral issued a token.
  * `kind: "contacts"` — how many fax numbers the contacts hold, and how
    many of them are valid North American numbers.
  * `kind: "history"`  — how many numbers faxes went to, how many faxes,
    how many delivered, and the newest fax's date.
  * `kind: "import"`   — how many distinct numbers the import would offer,
    and how many are already in the directory.
  * `kind: "summary"`  — `ok` is true only when every read worked, last.

Counts only: no names, no numbers, no patient data. A failed step prints
RingCentral's reason and the command exits non-zero.
"""
import json

from django.core.management.base import BaseCommand, CommandError

from emr import ringcentral_fax
from emr.models import FaxRecipient


class Command(BaseCommand):
    help = "Read-only check of the RingCentral fax credential and what the import would see."

    def _emit(self, **row):
        self.stdout.write(json.dumps(row))

    def handle(self, *args, **options):
        from apps.mobile_api.views import _normalize_fax_number

        ok = True
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

        numbers = set()
        try:
            contacts = ringcentral_fax.contact_fax_numbers()
            valid = {_normalize_fax_number(c['fax_number']) for c in contacts} - {None}
            numbers |= valid
            self._emit(
                kind='contacts', ok=True, fax_numbers=len(contacts),
                valid_numbers=len(valid),
                with_a_name=sum(1 for c in contacts if c['name']))
        except ringcentral_fax.FaxError as error:
            ok = False
            self._emit(kind='contacts', ok=False, reason=str(error)[:300])

        try:
            sent = ringcentral_fax.sent_fax_numbers()
            valid = {_normalize_fax_number(s['fax_number']) for s in sent} - {None}
            numbers |= valid
            self._emit(
                kind='history', ok=True, days=ringcentral_fax.HISTORY_DAYS,
                numbers=len(sent), valid_numbers=len(valid),
                faxes=sum(s['times_faxed'] for s in sent),
                delivered=sum(s['times_delivered'] for s in sent),
                with_a_name=sum(1 for s in sent if s['name']),
                newest=max((s['last_faxed'] for s in sent), default='')[:10])
        except ringcentral_fax.FaxError as error:
            ok = False
            self._emit(kind='history', ok=False, reason=str(error)[:300])

        listed = set(FaxRecipient.objects.filter(is_active=True).values_list('fax_number', flat=True))
        self._emit(
            kind='import', distinct_numbers=len(numbers),
            already_in_directory=len(numbers & listed),
            would_offer=len(numbers - listed))
        self._emit(kind='summary', ok=ok)
        if not ok:
            raise CommandError('A RingCentral read failed.')
