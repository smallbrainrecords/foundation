"""Changing a chart document's PDF in the app (2026-11-17).

Owner asks, same day: "the capacity for a user to edit a pdf (add my
signature, add text)"; "we need to be able to remove pages and edit a pdf
after it's been added to the patient's chart"; "staff can add my sig without
my approval".

The Mac makes the new PDF (text and a signature burned in, or pages taken
out) and uploads it whole; the server never reads or draws a PDF. Rules,
each load-bearing:

  * **Every earlier version is kept.** The file before each change is
    recorded on a `DocumentEdit` row and never deleted; the earliest change's
    `previous_file` is the document as it was filed, served by
    `before-edits`, and any version can be brought back (`restore`), which
    is itself a change that keeps the version it replaces.
  * **Staff only, on a chart the caller can open.** A patient, a stranger
    and a document that is not on the chart in the URL all get a JSON 404,
    so the app can tell a refusal from a server without these routes (an
    HTML 404).
  * **Whose signature.** The server cannot see what is drawn on a page; the
    app says whose signature it placed (`signature_of`). It may be the
    editor's own, or that of a physician the editor works for
    (`PhysicianTeam`) who can open this chart — staff place the physician's
    signature without his approval (owner decision). Anyone else is refused
    (400 `signature_not_allowed`). The row and the audit line say who placed
    it.
  * **A retry writes nothing twice**: `client_uuid` is unique, and a retried
    request answers with the first one (`already: true`).
  * **A change made on an old copy is refused** (409 `file_changed`): the
    app sends `base_file`, the stored file name it started from, and another
    Mac's change since then changed it. Saving anyway would replace that
    change, a signature included, with a file that never had it.
  * **Audit** on the chart through `_emit_document_audit`: "Signed document:
    <name>" (with "<physician>'s signature" when staff placed it), "Edited
    document: <name>", "Removed page 3 of <name>", "Restored an earlier
    version of document: <name>".
  * **The text is read again** after pages are removed or a version is
    restored: the stored text is cleared, so the document is listed as
    unread until a Mac reads it.
  * **Fax review page removal is refused once a document was changed here**
    (`fax_review` answers 409 `document_edited`): it cuts from the fax as
    received and would silently drop the change.

`DOCUMENT_EDIT_ENABLED=false` switches saving off (503
`document_edit_disabled`); the history stays readable.
"""
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from emr.models import Document, DocumentEdit, PhysicianTeam

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


def _json_list(text):
    try:
        value = json.loads(text or '[]')
    except ValueError:
        value = []
    return value if isinstance(value, list) else []


def _page_numbers(raw):
    """Page numbers from 1, unique and sorted, from a JSON list."""
    return sorted({p for p in _json_list(raw) if isinstance(p, int) and not isinstance(p, bool) and p >= 1})


def edit_json(edit):
    return {
        'id': edit.id,
        'kind': edit.kind,
        'edited_by_id': edit.edited_by_id,
        'edited_by_name': _display(edit.edited_by) if edit.edited_by_id else '',
        'edited_at': edit.edited_at.isoformat() if edit.edited_at else None,
        'signed': edit.signed,
        'signature_of_id': edit.signature_of_id,
        'signature_of_name': _display(edit.signature_of) if edit.signature_of_id else '',
        'text_count': edit.text_count,
        'pages': _json_list(edit.pages),
        'removed_pages': _json_list(edit.removed_pages),
        'restored_edit_id': edit.restored_edit_id,
    }


def _readable(request, patient_id):
    return api._fax_caller_is_staff(request.user) and api._assert_patient_access(request.user, patient_id)


def may_place_signature(editor, signer, patient_id):
    """The editor's own signature, or a physician's the editor works for
    who can open this chart (owner decision 2026-11-17: staff place the
    physician's signature without his approval)."""
    if signer is None:
        return False
    if signer.id == editor.id:
        return True
    return (api._role_of(signer) == 'physician'
            and PhysicianTeam.objects.filter(physician=signer, member=editor).exists()
            and api._assert_patient_access(signer, patient_id))


def _audit_line(name, *, kind, signed=False, signer=None, editor=None, removed=()):
    if kind == 'pages':
        pages = ', '.join(str(p) for p in removed)
        return f"Removed page{'s' if len(removed) != 1 else ''} {pages} of {name}"
    if kind == 'restore':
        return f"Restored an earlier version of document: {name}"
    if signed:
        if signer is not None and editor is not None and signer.id != editor.id:
            return f"Signed document: {name} with {_display(signer)}'s signature"
        return f"Signed document: {name}"
    return f"Edited document: {name}"


def _answer(doc, edit, already=False):
    return JsonResponse({'success': True, 'already': already, 'edit': edit_json(edit),
                         'file_path': doc.document.name if doc.document else '', 'file_size': doc.file_size})


def _clear_text(doc):
    """Pages moved or went: the stored text is stale until a Mac reads the
    file again (the document is then listed as unread)."""
    doc.extracted_text = None
    doc.extracted_text_at = None
    doc.extracted_text_version = None
    return ['extracted_text', 'extracted_text_at', 'extracted_text_version']


def _lock(patient_id, document_id, client_uuid, base_file):
    """Inside a transaction: the locked document, or a response to return.
    A retry of an earlier request answers with it; a change made on an old
    copy is refused."""
    return _lock_in(Document.objects.filter(patient_id=patient_id), document_id, client_uuid, base_file)


def _lock_in(base, document_id, client_uuid, base_file):
    """`_lock` over any set of documents: a chart's (`patient_id`) or the
    Office list's (`office__isnull=False`, apps.mobile_api.office)."""
    doc = base.select_for_update().filter(id=document_id).first()
    if doc is None:
        return None, _not_found()
    earlier = DocumentEdit.objects.filter(client_uuid=client_uuid).select_related(
        'edited_by', 'signature_of').first()
    if earlier is not None:
        if earlier.document_id != doc.id:
            return None, _refuse('client_uuid_reused', 409)
        return None, _answer(doc, earlier, already=True)
    if not doc.document:
        return None, _refuse('no_file', 409)
    if base_file and base_file != doc.document.name:
        return None, _refuse('file_changed', 409, file_path=doc.document.name)
    return doc, None


def save_document_edit(request, *, base, document_id, may_access, signer_allowed, audit, log_fields,
                       allow_upload=False):
    """The edit route's work, shared by charts and the Office list.

    `base` is the documents the route may touch; `may_access()` says whether
    the caller may change them; `signer_allowed(editor, signer)` whether a
    signature is theirs to place; `audit(doc, user, line)` writes the audit
    row (None writes none); `log_fields` are added to the log line.
    `allow_upload` accepts `kind=upload`: a copy edited outside the app,
    uploaded whole (the Office list's "replace with edited copy").
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
    uploaded_copy = allow_upload and str(request.POST.get('kind') or '').strip() == 'upload'
    signed = str(request.POST.get('signed') or '').lower() in ('1', 'true', 'yes')
    try:
        text_count = max(0, int(request.POST.get('text_count') or 0))
    except ValueError:
        text_count = 0
    pages = _page_numbers(request.POST.get('pages'))
    removed = _page_numbers(request.POST.get('removed_pages'))
    if uploaded_copy:
        # A whole new file: what was drawn on it is not the app's to say.
        signed, text_count, pages, removed = False, 0, [], []
    elif not signed and text_count == 0 and not removed:
        return _refuse('nothing_added', 400)
    if not may_access():
        return _not_found()
    signer = None
    if signed:
        raw_signer = str(request.POST.get('signature_of') or '').strip()
        if raw_signer:
            try:
                signer = User.objects.filter(id=int(raw_signer)).first()
            except ValueError:
                signer = None
        else:
            signer = request.user
        if not signer_allowed(request.user, signer):
            return _refuse('signature_not_allowed', 400)
    kind = 'upload' if uploaded_copy else ('pages' if removed else 'edit')
    base_file = str(request.POST.get('base_file') or '').strip()

    with transaction.atomic():
        doc, response = _lock_in(base, document_id, client_uuid, base_file)
        if response is not None:
            return response
        previous = doc.document.name
        doc.document = upload
        doc.file_size = upload.size
        fields = ['document', 'file_size']
        if removed or uploaded_copy:
            fields += _clear_text(doc)
        doc.save(update_fields=fields)
        edit = DocumentEdit.objects.create(
            document=doc, edited_by=request.user, kind=kind, signed=signed, signature_of=signer,
            text_count=text_count, pages=json.dumps(pages), removed_pages=json.dumps(removed),
            previous_file=previous, new_file=doc.document.name, client_uuid=client_uuid)
        if audit is not None:
            audit(doc, request.user, _audit_line(
                doc.document_name or 'document', kind=kind, signed=signed, signer=signer, editor=request.user,
                removed=removed))

    _log('document_edited', request, document_id=doc.id, kind=kind, signed=signed,
         signature_of=signer.id if signer else None, text_count=text_count, pages=pages, removed_pages=removed,
         **log_fields)
    return _answer(doc, edit)


def restore_document_edit(request, *, base, document_id, may_access, audit, log_fields):
    """The restore route's work, shared by charts and the Office list."""
    if request.method != 'POST':
        return _refuse('POST required', 405)
    if not api._fax_caller_is_staff(request.user):
        return _not_found()
    if not enabled():
        return _refuse('document_edit_disabled', 503)
    try:
        body = json.loads(request.body or b'{}')
    except ValueError:
        body = {}
    if not isinstance(body, dict):
        body = {}
    client_uuid = str(body.get('client_uuid') or '').strip()[:64]
    if not client_uuid:
        return _refuse('client_uuid_required', 400)
    try:
        edit_id = int(body.get('edit_id'))
    except (TypeError, ValueError):
        return _refuse('edit_required', 400)
    if not may_access():
        return _not_found()
    base_file = str(body.get('base_file') or '').strip()

    with transaction.atomic():
        doc, response = _lock_in(base, document_id, client_uuid, base_file)
        if response is not None:
            return response
        target = DocumentEdit.objects.filter(id=edit_id, document=doc).first()
        if target is None or not target.previous_file:
            return _refuse('edit_not_found', 404)
        version = target.previous_file
        if version == doc.document.name:
            return _refuse('already_current', 409)
        if not default_storage.exists(version):
            return _refuse('file_missing', 409)
        previous = doc.document.name
        doc.document.name = version
        try:
            doc.file_size = default_storage.size(version)
        except Exception:
            doc.file_size = None
        doc.save(update_fields=['document', 'file_size'] + _clear_text(doc))
        edit = DocumentEdit.objects.create(
            document=doc, edited_by=request.user, kind='restore', restored_edit=target,
            previous_file=previous, new_file=version, client_uuid=client_uuid)
        if audit is not None:
            audit(doc, request.user, _audit_line(doc.document_name or 'document', kind='restore'))

    _log('document_restored', request, document_id=doc.id, edit_id=edit_id, **log_fields)
    return _answer(doc, edit)


def edits_response(doc):
    """{edits: who changed this document, when and how, oldest first}."""
    edits = DocumentEdit.objects.filter(document=doc).select_related(
        'edited_by', 'signature_of').order_by('edited_at', 'id')
    return JsonResponse({'success': True, 'edits': [edit_json(e) for e in edits]})


def before_edits_response(doc):
    """The document's file as it was before its first change, or a JSON 404
    (`not_edited`) when nobody has changed it."""
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


@csrf_exempt
@login_required
@touches_patient_stamp
def mobile_document_edit(request, patient_id, document_id):
    """POST multipart {file, client_uuid, signed, signature_of, text_count,
    pages, removed_pages, base_file} -> the document's file becomes the new
    PDF; the file before it is kept.

    `signed` is "true" when a signature was placed and `signature_of` the id
    of the person whose it is (the uploader when left out); `text_count` is
    how many pieces of text were added and `pages` (JSON) the pages touched,
    from 1; `removed_pages` (JSON) the pages taken out, numbered in the file
    the change was made on; `base_file` that file's stored name
    (`file_path` from the chart's documents), checked when sent. A change
    that adds and removes nothing is refused.
    """
    return save_document_edit(
        request, base=Document.objects.filter(patient_id=patient_id), document_id=document_id,
        may_access=lambda: api._assert_patient_access(request.user, patient_id),
        signer_allowed=lambda editor, signer: may_place_signature(editor, signer, patient_id),
        audit=api._emit_document_audit, log_fields={'patient_id': int(patient_id)})


@csrf_exempt
@login_required
@touches_patient_stamp
def mobile_document_restore(request, patient_id, document_id):
    """POST JSON {edit_id, client_uuid, base_file} -> the document's file
    becomes the file as it was before that change. The file it replaces is
    kept, so a restore can itself be undone the same way."""
    return restore_document_edit(
        request, base=Document.objects.filter(patient_id=patient_id), document_id=document_id,
        may_access=lambda: api._assert_patient_access(request.user, patient_id),
        audit=api._emit_document_audit, log_fields={'patient_id': int(patient_id)})


@csrf_exempt
@login_required
def mobile_document_edits(request, patient_id, document_id):
    """GET -> {edits: who changed this document, when and how, oldest
    first}. Staff only. Read-only."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not _readable(request, patient_id):
        return _not_found()
    doc = Document.objects.filter(id=document_id, patient_id=patient_id).first()
    if doc is None:
        return _not_found()
    return edits_response(doc)


@csrf_exempt
@login_required
def mobile_document_before_edits(request, patient_id, document_id):
    """GET -> the document's file as it was before its first change. JSON 404
    (`not_edited`) when nobody has changed it. Staff only. Read-only."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not _readable(request, patient_id):
        return _not_found()
    doc = Document.objects.filter(id=document_id, patient_id=patient_id).first()
    if doc is None:
        return _not_found()
    return before_edits_response(doc)
