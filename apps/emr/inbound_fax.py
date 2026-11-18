"""Importing the faxes the clinic line receives into the unassigned pool
(inbound-fax plan, phase 1, 2026-11-16 — SBR1 PLAN_INBOUND_FAX_2026-11.md).

`import_new_faxes` lists the clinic line's received faxes in RingCentral
(`ringcentral_fax.inbound_faxes`), and for each one received after
`INBOUND_FAX_START` that has not been imported yet, downloads the PDF and
files it as a `Document` in the unassigned pool of the team named by
`INBOUND_FAX_TEAM_ID`. Staff then see it in the pool exactly as if it had
been uploaded from a Mac.

Rules, each load-bearing:

  * **Off unless configured.** `INBOUND_FAX_ENABLED`, a team that exists, a
    start moment with a time zone, and the RingCentral credential. Faxes
    received before the start were handled the old way (re-faxed and
    uploaded by hand) and are never imported, so turning this on cannot
    flood the pool with last week's faxes.
  * **Once per fax.** One `InboundFax` row per RingCentral message id
    (unique), locked while its PDF is fetched; the Document's `client_uuid`
    is derived from the same id. Two Macs and a scheduled job asking at the
    same moment import a fax once.
  * **Bounded passes.** At most `batch` downloads per pass, so the request
    that runs it stays short; the rest wait for the next pass. A 429 from
    RingCentral ends the pass without counting against the fax.
  * **Failures are counted, then given up.** A fax whose PDF cannot be
    fetched keeps its row with the error; after `MAX_ATTEMPTS` the importer
    stops asking and reports it as given up, so one bad fax cannot be
    retried forever.
  * **RingCentral is not a backup.** It keeps about a week of received faxes
    on this account (measured 2026-11-16), so the window read is a little
    over a week and the stored Document is the only lasting copy.
  * **A deleted fax stays deleted** (fixed 2026-11-18). Deleting the
    Document empties `InboundFax.document` (SET_NULL), and the importer used
    to read that as "not imported yet" and fetch the fax again on the next
    pass, as long as RingCentral still had it: in production 14 faxes came
    back after being deleted, one of them 7 times. `imported_on` is set in
    the same save that attaches the document, so a row with `imported_on`
    and no document had its document deleted; it is skipped, and counted as
    `deleted`.
  * **A stored fax leaves RingCentral** (owner, 2026-11-18: "ok to delete
    documents from ring central once we have downloaded"). The scheduled job
    moves every fax it finds stored here (`imported_on` set) from the clinic
    line's mailbox to RingCentral's Deleted folder: deleted, not purged, so
    RingCentral still holds it until it empties that folder. Only faxes the
    list shows as 'Alive' are sent: a second DELETE would purge. Only the
    job does it (`delete_batch`); the Macs' once-a-minute check stays short.
    It needs the app's EditMessages permission, read from the token's scope
    (`rc_delete: no_permission` until it is granted), and
    `INBOUND_FAX_DELETE_IMPORTED=false` switches it off.
"""
import datetime
import json
import logging
import re
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from emr import ringcentral_fax
from emr.models import Document, InboundFax

LOGGER = logging.getLogger('smallbrain.inbound_fax')

IMPORT_WINDOW_DAYS = 8
MAX_ATTEMPTS = 5
DEFAULT_BATCH = 5
# Stored faxes the job moves to RingCentral's Deleted folder per run. Deletes
# share RingCentral's "Medium" rate group (40 a minute) with downloads; in
# steady state a run deletes a few.
DELETE_PER_RUN = 20
DELETE_PERMISSION = 'EditMessages'
# Fixed namespace for the Documents' client_uuid: uuid5(namespace, message id).
_UUID_NAMESPACE = uuid.UUID('6f1c2f0e-7a4e-4b8e-9d55-3d1f0c2a9b71')


def _log(event, **fields):
    LOGGER.info(json.dumps(dict(
        severity='INFO', message=event, event=event,
        serviceContext={'service': 'smallbrain-api'}, **fields)))


def config():
    """{'ok', 'problem', 'team', 'start'}. `problem` is one of 'disabled',
    'no_credential', 'no_team', 'no_start' when `ok` is false."""
    result = {'ok': False, 'problem': None, 'team': None, 'start': None}
    if not getattr(settings, 'INBOUND_FAX_ENABLED', False):
        result['problem'] = 'disabled'
        return result
    if not ringcentral_fax.is_configured():
        result['problem'] = 'no_credential'
        return result
    team = User.objects.filter(id=getattr(settings, 'INBOUND_FAX_TEAM_ID', 0) or 0).first()
    if team is None:
        result['problem'] = 'no_team'
        return result
    start = parse_datetime(getattr(settings, 'INBOUND_FAX_START', '') or '')
    if start is None or timezone.is_naive(start):
        result['problem'] = 'no_start'
        return result
    result.update(ok=True, team=team, start=start)
    return result


def _received(fax):
    when = parse_datetime(fax.get('received') or '')
    if when is None:
        return None
    return timezone.make_aware(when, datetime.timezone.utc) if timezone.is_naive(when) else when


def display_number(number):
    digits = re.sub(r'\D', '', number or '')
    if len(digits) == 11 and digits.startswith('1'):
        digits = digits[1:]
    if len(digits) == 10:
        return '(%s) %s-%s' % (digits[:3], digits[3:6], digits[6:])
    return (number or '').strip()


def document_name(fax):
    """"Fax from <sender>": RingCentral's sender name when it has one, else
    the number. The Mac that opens the fax may replace it with a name read
    off the pages (the pool's auto-namer renames only a document still
    carrying this arrival name)."""
    sender = re.sub(r'[\x00-\x1f/\\:*?"<>|]+', ' ', fax.get('from_name') or '').strip()
    sender = re.sub(r'\s+', ' ', sender)[:80] or display_number(fax.get('from_number')) or 'an unknown number'
    return 'Fax from %s' % sender


def client_uuid_for(message_id):
    return uuid.uuid5(_UUID_NAMESPACE, 'ringcentral-fax:%s' % message_id)


def _pdf_attachment(fax):
    for attachment in fax.get('attachments') or []:
        if 'pdf' in (attachment.get('content_type') or '').lower() and attachment.get('id') is not None:
            return attachment
    return None


def _import_one(fax, team, trigger):
    """'imported' | 'already' | 'failed' | 'given_up' | 'rate_limited'."""
    message_id = str(fax['id'])
    with transaction.atomic():
        row, _ = InboundFax.objects.select_for_update().get_or_create(
            rc_message_id=message_id,
            defaults={
                'received_at': _received(fax),
                'from_number': (fax.get('from_number') or '')[:32],
                'from_name': (fax.get('from_name') or '')[:255],
                'page_count': fax.get('pages'),
            })
        if row.document_id:
            return 'already'
        if row.imported_on is not None:
            # Imported once, then its document was deleted: never again.
            return 'deleted'
        if row.attempts >= MAX_ATTEMPTS:
            return 'given_up'

        attachment = _pdf_attachment(fax)
        if attachment is None:
            types = sorted({a.get('content_type') or '?' for a in fax.get('attachments') or []})
            row.attempts = MAX_ATTEMPTS
            row.last_error = 'No PDF in this fax (attachments: %s).' % (', '.join(types) or 'none')
            row.save(update_fields=['attempts', 'last_error'])
            _log('inbound_fax_given_up', rc_message_id=message_id, error=row.last_error, trigger=trigger)
            return 'given_up'

        try:
            data, _content_type = ringcentral_fax.fax_attachment(message_id, attachment['id'])
            if not data.startswith(b'%PDF'):
                raise ringcentral_fax.FaxError('RingCentral sent something that is not a PDF.')
        except ringcentral_fax.FaxError as error:
            if error.status == 429:
                return 'rate_limited'
            row.attempts += 1
            row.last_error = str(error)[:500]
            row.save(update_fields=['attempts', 'last_error'])
            gave_up = row.attempts >= MAX_ATTEMPTS
            _log('inbound_fax_given_up' if gave_up else 'inbound_fax_failed',
                 rc_message_id=message_id, attempts=row.attempts, status=error.status,
                 error=row.last_error[:200], trigger=trigger)
            return 'given_up' if gave_up else 'failed'

        name = document_name(fax)
        file_name = name + '.pdf'
        doc = Document.objects.create(
            document=ContentFile(data, name=file_name),
            document_name=name,
            author=team,
            patient=None,
            team=team,
            file_size=len(data),
            original_file_name=file_name,
            client_uuid=client_uuid_for(message_id),
        )
        row.document = doc
        row.imported_on = timezone.now()
        row.last_error = ''
        row.save(update_fields=['document', 'imported_on', 'last_error'])

    digits = re.sub(r'\D', '', fax.get('from_number') or '')
    _log('inbound_fax_imported', rc_message_id=message_id, document_id=doc.id, team_id=team.id,
         pages=fax.get('pages'), from_last_four=digits[-4:], trigger=trigger)
    return 'imported'


def import_new_faxes(batch=DEFAULT_BATCH, trigger='app', days=IMPORT_WINDOW_DAYS, dry_run=False,
                     delete_batch=0):
    """One import pass. With `delete_batch` above 0 (the scheduled job), it
    then moves up to that many stored faxes to RingCentral's Deleted folder
    (`remove_stored_from_ringcentral`). Returns a summary dict:

      configured   — false (with `problem`) when the import is off
      listed       — faxes received since the start that RingCentral holds
      imported     — stored this pass
      already      — imported by an earlier pass
      waiting      — left for a later pass (batch reached, or rate limited)
      failed       — could not be fetched this pass (will be retried)
      given_up     — no longer retried; the row keeps the reason
      rate_limited — RingCentral asked us to slow down; the pass stopped
      complete     — RingCentral's list was read to its end
      would_import — with `dry_run`: how many this pass would fetch (nothing
                     is downloaded or written)
      rc_delete, rc_deleted, rc_waiting, would_delete_from_ringcentral —
                     see `remove_stored_from_ringcentral`

    Listing the mailbox can raise `ringcentral_fax.FaxError`; the caller
    reports it. Downloads never raise: each fax's outcome is counted.
    """
    cfg = config()
    if not cfg['ok']:
        return {'configured': False, 'problem': cfg['problem']}

    trace = {}
    faxes = ringcentral_fax.inbound_faxes(days=days, trace=trace)
    eligible = []
    for fax in faxes:
        when = _received(fax)
        if fax.get('id') is not None and when is not None and when >= cfg['start']:
            eligible.append((when, fax))
    eligible.sort(key=lambda pair: pair[0])

    summary = {'configured': True, 'listed': len(eligible), 'imported': 0, 'already': 0,
               'deleted': 0, 'waiting': 0, 'failed': 0, 'given_up': 0, 'rate_limited': False,
               'complete': bool(trace.get('complete'))}
    known = dict(
        (message_id, (document_id, attempts, imported_on))
        for message_id, document_id, attempts, imported_on in
        InboundFax.objects.filter(rc_message_id__in=[str(f['id']) for _, f in eligible])
        .values_list('rc_message_id', 'document_id', 'attempts', 'imported_on'))
    tried = 0
    for _, fax in eligible:
        document_id, attempts, imported_on = known.get(str(fax['id']), (None, 0, None))
        if document_id:
            summary['already'] += 1
            continue
        if imported_on is not None:
            # Imported once, then someone deleted the document. Taking a
            # place in the batch would fetch it back from RingCentral.
            summary['deleted'] += 1
            continue
        if attempts >= MAX_ATTEMPTS:
            # Given up on an earlier pass: counted, not retried, and it
            # takes no place in this pass's batch.
            summary['given_up'] += 1
            continue
        if summary['rate_limited'] or tried >= batch:
            summary['waiting'] += 1
            continue
        tried += 1
        if dry_run:
            summary['would_import'] = summary.get('would_import', 0) + 1
            continue
        outcome = _import_one(fax, cfg['team'], trigger)
        if outcome == 'rate_limited':
            summary['rate_limited'] = True
            summary['waiting'] += 1
        else:
            summary[outcome] += 1
    if summary['rate_limited']:
        # Deletes share the rate group RingCentral just said to slow down in.
        summary.update(rc_delete='rate_limited', rc_deleted=0)
    else:
        summary.update(remove_stored_from_ringcentral(
            [fax for _, fax in eligible], delete_batch, trigger=trigger, dry_run=dry_run))
    return summary


def remove_stored_from_ringcentral(faxes, limit, trigger='job', dry_run=False):
    """Moves up to `limit` of `faxes` (the pass's list) that are stored here
    to RingCentral's Deleted folder, oldest first. Stored means `imported_on`
    is set: the PDF was saved as a Document, which a person may have deleted
    since. A fax still waiting, failed or given up stays in RingCentral, and
    so does one the list does not show as 'Alive' (deleting it again would
    purge it). Returns:

      rc_delete  — 'not_this_pass' (limit 0: a Mac's check), 'off'
                   (INBOUND_FAX_DELETE_IMPORTED=false), 'dry_run',
                   'nothing_to_delete', 'no_permission' (the token lacks
                   EditMessages), 'done', or why it stopped: 'not_allowed'
                   (403), 'rate_limited' (429), 'failed'
      rc_deleted — moved to the Deleted folder this pass
      rc_waiting — stored faxes still in RingCentral after this pass
      would_delete_from_ringcentral — with `dry_run`

    Never raises: a refused or failed delete is logged, and the next run
    tries again from a fresh list.
    """
    result = {'rc_delete': 'not_this_pass', 'rc_deleted': 0}
    if limit <= 0:
        return result
    if not getattr(settings, 'INBOUND_FAX_DELETE_IMPORTED', False):
        result['rc_delete'] = 'off'
        return result
    alive = [str(fax['id']) for fax in faxes
             if fax.get('id') is not None and fax.get('availability') == 'Alive']
    stored = dict(InboundFax.objects.filter(rc_message_id__in=alive, imported_on__isnull=False)
                  .values_list('rc_message_id', 'document_id'))
    candidates = [message_id for message_id in alive if message_id in stored]
    result['rc_waiting'] = len(candidates)
    if dry_run:
        result.update(rc_delete='dry_run', would_delete_from_ringcentral=len(candidates))
        return result
    if not candidates:
        result['rc_delete'] = 'nothing_to_delete'
        return result
    try:
        granted = ringcentral_fax.granted_permissions()
    except (ringcentral_fax.FaxError, ringcentral_fax.FaxNotConfigured) as error:
        result['rc_delete'] = 'failed'
        _log('inbound_fax_ringcentral_delete_failed', error=str(error)[:200], trigger=trigger)
        return result
    if granted is not None and DELETE_PERMISSION not in granted:
        result['rc_delete'] = 'no_permission'
        return result
    result['rc_delete'] = 'done'
    for message_id in candidates[:limit]:
        try:
            ringcentral_fax.move_fax_to_deleted(message_id)
        except ringcentral_fax.FaxError as error:
            if error.status == 404:
                # No longer in RingCentral: nothing left to delete.
                result['rc_waiting'] -= 1
                continue
            result['rc_delete'] = {403: 'not_allowed', 429: 'rate_limited'}.get(error.status, 'failed')
            _log('inbound_fax_ringcentral_delete_failed', rc_message_id=message_id, status=error.status,
                 error=str(error)[:200], trigger=trigger)
            break
        result['rc_deleted'] += 1
        result['rc_waiting'] -= 1
        _log('inbound_fax_removed_from_ringcentral', rc_message_id=message_id,
             document_id=stored[message_id], trigger=trigger)
    return result
