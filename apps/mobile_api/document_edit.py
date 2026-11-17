"""Editing a chart document's PDF in the app (2026-11-17; owner ask: "the
capacity for a user to edit a pdf (add my signature, add text)").

The Mac burns what was added into a new PDF and uploads it whole; the server
never reads or draws a PDF. Rules, each load-bearing:

  * **Every earlier version is kept.** The file as it was before each edit
    is recorded on a `DocumentEdit` row and never deleted; the earliest
    edit's `previous_file` is the document as it was before anyone edited
    it, served by `before-edits`.
  * **Staff only, on a chart the caller can open.** A patient, a stranger
    and a document that is not on the chart in the URL all get a JSON 404,
    so the app can tell a refusal from a server without these routes (an
    HTML 404).
  * **A signature is the editor's own.** The server cannot see what is drawn
    on a page. The app offers each person only their own signature, and the
    row records who uploaded the signed version (`signed`, `edited_by`).
  * **A retry writes nothing twice**: `client_uuid` is unique, and a retried
    upload answers with the first one (`already: true`).
  * **An edit made on an old copy is refused** (409 `file_changed`): the app
    sends `base_file`, the stored file name it started from, and another
    Mac's edit since then changed it. Saving anyway would replace that
    edit, a signature included, with a file that never had it.
  * **Audit**: "Signed document: <name>" when a signature was placed, else
    "Edited document: <name>", through `_emit_document_audit` like a rename.
  * **Pages can no longer be removed once a document was edited**
    (`fax_review` answers 409 `document_edited`): page removal cuts from the
    fax as received and would silently drop the signature.

`DOCUMENT_EDIT_ENABLED=false` switches saving off (503
`document_edit_disabled`); the history stays readable.
"""
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from emr.models import Document, DocumentEdit

from . import views as api
from .views import touches_patient_stamp

LOGGER = logging.getLogger('smallbrain.document_edit')


def enabled():
    return bool(getattr(settings, 'DOCUMENT_EDIT_ENABLED', True))


def _log(event, request, **fields):
    LOGGER.info(json.dumps(dict(
        severity='INFO', message=event, event=event, actor_id=request.user.id,
        serviceContext={'service': 'smallbrain-api'}, **fields)))


def _refuse(error, status, **extra):
    return JsonResponse(dict(success=False, error=error, **extra), status=status)


def _not_found():
    return _refuse('not_found', 404)


def _display(user):
    if user is None:
        return ''
    return user.get_full_name() or user.username


def _pages(edit):
    try:
        pages = json.loads(edit.pages or '[]')
    except ValueError:
        pages = []
    return pages if isinstance(pages, list) else []


def edit_json(edit):
    return {
        'id': edit.id,
        'edited_by_id': edit.edited_by_id,
        'edited_by_name': _display(edit.edited_by) if edit.edited_by_id else '',
        'edited_at': edit.edited_at.isoformat() if edit.edited_at else None,
        'signed': edit.signed,
        'text_count': edit.text_count,
        'pages': _pages(edit),
    }


def _readable(request, patient_id):
    return api._fax_caller_is_staff(request.user) and api._assert_patient_access(request.user, patient_id)


@csrf_exempt
@login_required
@touches_patient_stamp
def mobile_document_edit(request, patient_id, document_id):
    """POST multipart {file, client_uuid, signed, text_count, pages,
    base_file} -> the document's file becomes the edited PDF; the file before
    it is kept.

    `signed` is "true" when the edit placed the uploader's own signature;
    `text_count` is how many pieces of text were added; `pages` (JSON) the
    page numbers touched, from 1; `base_file` the stored file name the edit
    was made on (`file_path` from the chart's documents), checked when sent.
    An edit that adds nothing is refused.
    """
    if request.method != 'POST':
        return _refuse('POST required', 405)
    if not api._fax_caller_is_staff(request.user):
        return _not_found()
    if not enabled():
        return _refuse('document_edit_disabled', 503)
    upload = request.FILES.get('file')
    if upload is None:
        return _refuse('file_required', 400)
    head = upload.read(5)
    upload.seek(0)
    if not head.startswith(b'%PDF'):
        return _refuse('not_a_pdf', 400)
    client_uuid = str(request.POST.get('client_uuid') or '').strip()[:64]
    if not client_uuid:
        return _refuse('client_uuid_required', 400)
    signed = str(request.POST.get('signed') or '').lower() in ('1', 'true', 'yes')
    try:
        text_count = max(0, int(request.POST.get('text_count') or 0))
    except ValueError:
        text_count = 0
    try:
        pages = json.loads(request.POST.get('pages') or '[]')
    except ValueError:
        pages = []
    if not isinstance(pages, list):
        pages = []
    pages = sorted({p for p in pages if isinstance(p, int) and not isinstance(p, bool) and p >= 1})
    if not signed and text_count == 0:
        return _refuse('nothing_added', 400)
    if not api._assert_patient_access(request.user, patient_id):
        return _not_found()

    with transaction.atomic():
        doc = Document.objects.select_for_update().filter(id=document_id, patient_id=patient_id).first()
        if doc is None:
            return _not_found()
        earlier = DocumentEdit.objects.filter(client_uuid=client_uuid).select_related('edited_by').first()
        if earlier is not None:
            if earlier.document_id != doc.id:
                return _refuse('client_uuid_reused', 409)
            return JsonResponse({'success': True, 'already': True, 'edit': edit_json(earlier),
                                 'file_path': doc.document.name if doc.document else '',
                                 'file_size': doc.file_size})
        if not doc.document:
            return _refuse('no_file', 409)
        base_file = str(request.POST.get('base_file') or '').strip()
        if base_file and base_file != doc.document.name:
            return _refuse('file_changed', 409, file_path=doc.document.name)
        previous = doc.document.name
        doc.document = upload
        doc.file_size = upload.size
        doc.save(update_fields=['document', 'file_size'])
        edit = DocumentEdit.objects.create(
            document=doc, edited_by=request.user, signed=signed, text_count=text_count,
            pages=json.dumps(pages), previous_file=previous, new_file=doc.document.name,
            client_uuid=client_uuid)
        name = doc.document_name or 'document'
        api._emit_document_audit(
            doc, request.user, f"Signed document: {name}" if signed else f"Edited document: {name}")
        answer = edit_json(edit)

    _log('document_edited', request, document_id=doc.id, patient_id=int(patient_id), signed=signed,
         text_count=text_count, pages=pages)
    return JsonResponse({'success': True, 'edit': answer, 'file_path': doc.document.name,
                         'file_size': doc.file_size})


@csrf_exempt
@login_required
def mobile_document_edits(request, patient_id, document_id):
    """GET -> {edits: who edited this document, when, and whether they
    signed it, oldest first}. Staff only. Read-only."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not _readable(request, patient_id):
        return _not_found()
    doc = Document.objects.filter(id=document_id, patient_id=patient_id).first()
    if doc is None:
        return _not_found()
    edits = DocumentEdit.objects.filter(document=doc).select_related('edited_by').order_by('edited_at', 'id')
    return JsonResponse({'success': True, 'edits': [edit_json(e) for e in edits]})


@csrf_exempt
@login_required
def mobile_document_before_edits(request, patient_id, document_id):
    """GET -> the document's file as it was before its first edit. JSON 404
    (`not_edited`) when nobody has edited it. Staff only. Read-only."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not _readable(request, patient_id):
        return _not_found()
    doc = Document.objects.filter(id=document_id, patient_id=patient_id).first()
    if doc is None:
        return _not_found()
    first = DocumentEdit.objects.filter(document=doc).order_by('edited_at', 'id').first()
    if first is None or not first.previous_file:
        return _refuse('not_edited', 404)
    try:
        handle = default_storage.open(first.previous_file, 'rb')
    except Exception:
        LOGGER.exception('the file before the first edit could not be opened')
        return _refuse('file_missing', 404)
    response = FileResponse(handle, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="before-edits.pdf"'
    return response
