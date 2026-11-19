"""Faxing chart documents (2026-11-18).

Owner asks, same day: Fax... beside Print on a chart document, and "Fax
selected" from the Docs list's multi-select (several documents, one fax,
one cover page). Every staff role may fax; the cover page is on by default
and drawn on the Mac, which sends the finished PDF.

Rules, each load-bearing:

  * **A disclosure is logged on the chart.** Each document faxed writes
    "Faxed document: <name> to <recipient> (fax 586-555-1234)" through
    `_emit_document_audit`, then a delivered or failed row when the fax
    settles (`views._settle_fax`).
  * **The same sending rules as requisitions**: a directory entry only, the
    client_uuid claimed before RingCentral is called so a retry never faxes
    twice, 502 `fax_send_failed` when RingCentral did not take it (nothing is
    logged on the chart then: nothing left the practice).
  * **The PDF as sent is kept** (`FaxTransmission.file_path`): it is the
    record of what left, and when the fax fails later the sender gets it
    back in Office ("Documents for you"), with the reason, to send again.
  * Every document must be on this chart (400 `document_not_on_chart`).
"""
import json
import logging
import uuid

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from emr.models import Document, FaxTransmission
from emr.storable import delete_stored_files

from . import views as api
from .views import touches_patient_stamp

LOGGER = logging.getLogger('smallbrain.chart_fax')

MAX_DOCUMENTS = 50


def _log(event, request, **fields):
    LOGGER.info(json.dumps(dict(
        severity='INFO', message=event, event=event, user_id=request.user.id,
        serviceContext={'service': 'smallbrain-api'}, **fields)))


def _refuse(error, status, **extra):
    return JsonResponse(dict({'error': error}, **extra), status=status)


def document_ids_of(row):
    try:
        ids = json.loads(row.document_ids or '[]')
    except ValueError:
        return []
    return [i for i in ids if isinstance(i, int)]


def faxed_line(doc, recipient_name, fax_number):
    return 'Faxed document: %s to %s (fax %s)' % (
        doc.document_name or 'document', recipient_name, api._display_fax_number(fax_number))


@csrf_exempt
@login_required
@touches_patient_stamp
def mobile_fax_chart_documents(request, patient_id):
    """POST multipart {file, client_uuid, recipient_id, document_ids, cover}
    -> {success, transmission}. `file` is the PDF to send as the Mac built
    it: the documents in order, the cover page in front when `cover` is "1"
    (RingCentral adds none)."""
    from emr import ringcentral_fax
    from emr.models import FaxRecipient

    if not api._fax_caller_is_staff(request.user) or not api._assert_patient_access(request.user, patient_id):
        return _refuse('not_found', 404)
    if request.method != 'POST':
        return _refuse('POST required', 405)
    # The URL hands it over as text; the row and its JSON need the number.
    patient_id = int(patient_id)
    client_uuid = (request.POST.get('client_uuid') or '').strip()
    if not client_uuid or len(client_uuid) > 36:
        return _refuse('client_uuid_required', 400)
    try:
        wanted = json.loads(request.POST.get('document_ids') or '')
    except ValueError:
        return _refuse('documents_required', 400)
    if (not isinstance(wanted, list) or not wanted or len(wanted) > MAX_DOCUMENTS
            or not all(isinstance(i, int) and not isinstance(i, bool) for i in wanted)
            or len(set(wanted)) != len(wanted)):
        return _refuse('documents_required', 400)
    docs = {d.id: d for d in Document.objects.filter(id__in=wanted, patient_id=patient_id)}
    if len(docs) != len(wanted):
        return _refuse('document_not_on_chart', 400)
    try:
        recipient = FaxRecipient.objects.get(id=int(request.POST.get('recipient_id') or 0), is_active=True)
    except (FaxRecipient.DoesNotExist, ValueError):
        return _refuse('recipient_not_found', 400)
    upload = request.FILES.get('file')
    if upload is None:
        return _refuse('file_required', 400)
    if upload.size > api._FAX_MAX_BYTES:
        return _refuse('file_too_large', 400)
    pdf_bytes = upload.read()
    if not pdf_bytes.startswith(b'%PDF'):
        return _refuse('not_a_pdf', 400)
    if not ringcentral_fax.is_configured():
        return _refuse('fax_not_configured', 503)
    cover = str(request.POST.get('cover') or '').lower() in ('1', 'true', 'yes')
    ids_json = json.dumps(wanted)

    try:
        with transaction.atomic():
            row = FaxTransmission.objects.create(
                client_uuid=client_uuid, patient_id=patient_id, document=None, document_ids=ids_json,
                sender=request.user, recipient=recipient, recipient_name=recipient.name,
                fax_number=recipient.fax_number, todo_ids='[]', status=FaxTransmission.SENDING)
    except IntegrityError:
        row = FaxTransmission.objects.get(client_uuid=client_uuid)
        if row.patient_id != patient_id or document_ids_of(row) != wanted:
            return _refuse('client_uuid_reused', 409)
        if row.rc_message_id:
            # Already with RingCentral: a retry of a request whose answer
            # was lost. Never fax twice.
            return JsonResponse({'success': True, 'replayed': True,
                                 'transmission': api._fax_transmission_json(row)})
        age = (timezone.now() - row.created_on).total_seconds()
        if row.status == FaxTransmission.SENDING and age < api._FAX_SENDING_GRACE_SECONDS:
            return _refuse('fax_in_progress', 409)
        row.recipient = recipient
        row.recipient_name = recipient.name
        row.fax_number = recipient.fax_number
        row.sender = request.user
        row.status = FaxTransmission.SENDING
        row.error = ''
        row.save()

    # Kept before RingCentral is asked, so a fax that fails later still has
    # the pages to hand back.
    stored = default_storage.save('faxes/%s.pdf' % uuid.uuid4().hex, ContentFile(pdf_bytes))
    superseded = [row.file_path] if row.file_path else []
    row.file_path = stored
    row.save(update_fields=['file_path'])
    delete_stored_files(superseded)

    try:
        sent = ringcentral_fax.send_fax(pdf_bytes, recipient.fax_number, filename='records.pdf')
    except (ringcentral_fax.FaxError, ringcentral_fax.FaxNotConfigured) as error:
        row.status = FaxTransmission.FAILED
        row.error = str(error)[:500]
        row.settled_on = timezone.now()
        # Nothing left the practice: no copy to keep.
        delete_stored_files([row.file_path])
        row.file_path = ''
        row.save()
        _log('chart_fax_not_accepted', request, patient_id=patient_id, transmission_id=row.id,
             recipient_id=recipient.id, documents=len(wanted), error=row.error)
        return _refuse('fax_send_failed', 502, detail=row.error)

    row.rc_message_id = sent['message_id']
    row.rc_status = sent.get('rc_status') or ''
    row.page_count = sent.get('page_count')
    row.status = FaxTransmission.QUEUED
    row.save()
    for document_id in wanted:
        api._emit_document_audit(docs[document_id], request.user,
                                 faxed_line(docs[document_id], recipient.name, recipient.fax_number))
    _log('chart_fax_queued', request, patient_id=patient_id, transmission_id=row.id,
         recipient_id=recipient.id, fax_number=recipient.fax_number, documents=len(wanted), cover=cover,
         rc_message_id=row.rc_message_id)
    if sent.get('state') in ('delivered', 'failed'):
        row = api._settle_fax(row.id, sent)
    return JsonResponse({'success': True, 'transmission': api._fax_transmission_json(row)})


def settle_chart_fax(row, state, activity):
    """`views._settle_fax` for a fax of chart documents: the delivered or
    failed line on the chart, for each document still there; and when it
    failed, the pages as sent go to the sender's Office list with the
    reason. Called inside the settle transaction."""
    ids = document_ids_of(row)
    docs = list(Document.objects.filter(id__in=ids, patient_id=row.patient_id))
    names = [d.document_name or 'document' for d in docs]
    label = names[0] if len(names) == 1 else '%d documents' % len(ids)
    line = activity.replace('Fax to ', 'Fax of %s to ' % label, 1)
    for doc in docs:
        api._emit_document_audit(doc, row.sender, line)
    if state == 'failed' and row.sender_id and row.file_path:
        _hand_failed_pages_back(row, line)


def _hand_failed_pages_back(row, line):
    from emr.models import OfficeDocument, OfficeHandoff
    from emr.storable import stored_file_exists

    if not stored_file_exists(row.file_path):
        LOGGER.warning('a failed chart fax has no stored pages to hand back: %s', row.id)
        return
    with default_storage.open(row.file_path, 'rb') as handle:
        data = handle.read()
    now = timezone.now()
    copy = Document.objects.create(
        document=ContentFile(data, name='failed-fax.pdf'),
        document_name=('Fax to %s (failed)' % row.recipient_name)[:255],
        author=row.sender, patient=None, team=None, file_size=len(data), original_file_name='failed-fax.pdf')
    OfficeDocument.objects.create(
        document=copy, moved_by=row.sender, moved_at=now, source=OfficeDocument.CHART, note=line,
        source_patient_id=row.patient_id)
    OfficeHandoff.objects.create(document=copy, user_id=row.sender_id, handed_by_id=row.sender_id,
                                 handed_at=now, note=line)
