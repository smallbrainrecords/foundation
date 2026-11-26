"""The Office list (2026-11-18): documents that belong on no chart.

Staff pass around office business — audit requests, forms to fill in and fax
back — that never goes on a chart. Owner decisions, same day:

  * **It replaces the fax review's "set aside" and "do it later".** Both
    states are retired; their routes stay for Macs on build 86 and now move
    the fax here (`fax_review.mobile_fax_review_later` / `_set_aside`).
  * **Every staff member sees the list.** Patients never: they get a JSON
    404, like every refusal here (never 403 — the app reads 403 as signed
    out).
  * **A document stays until someone deletes it, files it to a chart, or
    sends it back to the unassigned pool.** Nothing expires. Filing straight
    from Office (`to-chart`, owner ask 2026-11-18: "we will need a way to
    assign a document to a patient in the office section") does what the
    pool's assign does: the chart's "Added document" audit (after "Renamed
    document" when the name changed), the chart's stamp, no review.
  * **Any staff member may delete**, permanently: the file, every earlier
    version and the fax as received go with the row. The app warns first.
  * **A document can be handed to several people** (`OfficeHandoff`). Each
    person sees it on their home page until they mark their part done; the
    document stays in Office either way.
  * **Faxing out** sends the PDF the Mac built — the document with its
    generated cover page in front — through the clinic's RingCentral line,
    recorded as a `FaxTransmission` naming the document. A fax that fails is
    handed back to its sender (`_settle_fax`), so the failure reaches them.
  * **Editing** reuses the chart document editor's routes
    (`document_edit.save_document_edit`): text, a date, a signature, pages
    taken out, or a copy edited outside the app uploaded whole. Every
    version is kept; a change made on an old copy is refused (409
    `file_changed`). A signature is the editor's own or that of a physician
    they work for. There is no chart, so no chart audit row; the log line is
    the record.

A document is in Office exactly when its `OfficeDocument` row exists. The
pool list leaves those documents out.

`OFFICE_ENABLED=false` switches it off: the list answers `enabled: false`
and every write answers 503 `office_disabled`.
"""
import json
import logging
import os
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from emr.models import (
    Document, DocumentEdit, DocumentReview, FaxTransmission, OfficeDocument, OfficeHandoff, PhysicianTeam,
)
from emr.mutation_stamp import touch_patient_stamp
from emr.storable import delete_stored_files, document_files

from . import document_edit
from . import fax_review
from . import views as api

LOGGER = logging.getLogger('smallbrain.office')

MAX_NOTE = 2000
MAX_NAME = 255
MAX_HANDOFFS = 25


def enabled():
    return bool(getattr(settings, 'OFFICE_ENABLED', True))


def _log(event, request, **fields):
    LOGGER.info(json.dumps(dict(
        severity='INFO', message=event, event=event, actor_id=request.user.id,
        serviceContext={'service': 'smallbrain-api'}, **fields)))


def _refuse(error, status, **extra):
    return JsonResponse(dict(success=False, error=error, **extra), status=status)


def _not_found():
    return _refuse('not_found', 404)


def _gate(request, method, write=True):
    """The checks every route shares. Returns a response to send, or None."""
    if not api._fax_caller_is_staff(request.user):
        return _not_found()
    if request.method != method:
        return _refuse('%s required' % method, 405)
    if write and not enabled():
        return _refuse('office_disabled', 503)
    return None


def _body(request):
    try:
        body = json.loads(request.body or b'{}')
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def _display(user):
    if user is None:
        return ''
    return user.get_full_name() or user.username


def _iso(value):
    return value.isoformat() if value else None


def _note(raw):
    return str(raw or '').strip()[:MAX_NOTE]


def _staff_users():
    """Everyone a document can be handed to: active staff, by name."""
    return User.objects.filter(
        is_active=True, profile__role__in=api._SEARCH_STAFF_ROLES,
    ).order_by('last_name', 'first_name', 'username')


# ---------------------------------------------------------------------------
# What the app reads
# ---------------------------------------------------------------------------

def handoff_json(row):
    return {
        'user_id': row.user_id,
        'name': _display(row.user),
        'handed_by_id': row.handed_by_id,
        'handed_by_name': _display(row.handed_by) if row.handed_by_id else '',
        'handed_at': _iso(row.handed_at),
        'note': row.note,
        'seen_at': _iso(row.seen_at),
        'done_at': _iso(row.done_at),
    }


def fax_json(row):
    return {
        'id': row.id,
        'recipient_name': row.recipient_name,
        'fax_number': row.fax_number,
        'display_number': api._display_fax_number(row.fax_number),
        'status': row.status,
        'error': row.error,
        'page_count': row.page_count,
        'sender_name': _display(row.sender) if row.sender_id else '',
        'created_on': _iso(row.created_on),
        'settled_on': _iso(row.settled_on),
    }


def office_json(doc, handoffs=None, faxes=None, edited=None):
    office = doc.office
    if handoffs is None:
        handoffs = list(OfficeHandoff.objects.filter(document=doc).select_related('user', 'handed_by'))
    if faxes is None:
        faxes = list(FaxTransmission.objects.filter(document=doc).select_related('sender').order_by('-created_on'))
    if edited is None:
        edited = DocumentEdit.objects.filter(document=doc).exists()
    inbound = api._inbound_fax_fields(doc)
    return {
        'id': doc.id,
        'document_name': doc.document_name or '',
        # The stored name: a new version changes it, which is how a Mac knows
        # its cached copy is old.
        'file_path': doc.document.name if doc.document else '',
        'file_name': os.path.basename(doc.document.name) if doc.document else '',
        'original_file_name': doc.original_file_name,
        'mime_type': doc.file_mime_type(),
        'file_size': doc.file_size,
        'created_on': _iso(doc.created_on),
        'team_id': doc.team_id,
        'moved_by_id': office.moved_by_id,
        'moved_by_name': _display(office.moved_by) if office.moved_by_id else '',
        'moved_at': _iso(office.moved_at),
        'source': office.source,
        'note': office.note,
        # A copy of a chart document, or the pages of a chart fax that
        # failed (2026-11-18): the chart it came from.
        'source_patient_id': office.source_patient_id,
        'source_patient_name': _display(office.source_patient) if office.source_patient_id else '',
        'edited': bool(edited),
        'handoffs': [handoff_json(h) for h in handoffs],
        'faxes': [fax_json(f) for f in faxes],
        # Received on the clinic line (emr.inbound_fax), when and how many
        # pages; None for a document from a Mac.
        'received_by_fax': inbound['source'] == 'ringcentral',
        'received_at': inbound['received_at'],
        'page_count': inbound['page_count'],
    }


def _office_documents():
    return Document.objects.filter(office__isnull=False).select_related(
        'office', 'office__moved_by', 'office__source_patient', 'inbound_fax')


@csrf_exempt
@login_required
def mobile_office_documents(request):
    """GET -> {enabled, documents, people, me}.

    `documents`: every Office document, the most recently moved in first,
    each with its hand-offs (who, by whom, the note, seen, done) and its
    faxes (newest first). Queued faxes are asked about here (at most every
    few seconds each), so their status settles whoever is looking.
    `people`: the active staff a document can be handed to.
    """
    refusal = _gate(request, 'GET', write=False)
    if refusal:
        return refusal
    if not enabled():
        return JsonResponse({'success': True, 'enabled': False})

    docs = list(_office_documents().order_by('-office__moved_at', '-id'))
    ids = [d.id for d in docs]
    handoffs, faxes = {}, {}
    # Faxes first: settling a failed one hands the document back to its
    # sender, and that hand-off belongs in this same answer.
    for row in FaxTransmission.objects.filter(document_id__in=ids).select_related(
            'sender').order_by('-created_on'):
        if row.status == FaxTransmission.QUEUED:
            row = api._refresh_fax(row)
        faxes.setdefault(row.document_id, []).append(row)
    for row in OfficeHandoff.objects.filter(document_id__in=ids).select_related(
            'user', 'handed_by').order_by('handed_at', 'id'):
        handoffs.setdefault(row.document_id, []).append(row)
    edited = set(DocumentEdit.objects.filter(document_id__in=ids).values_list('document_id', flat=True))

    return JsonResponse({
        'success': True,
        'enabled': True,
        'me': request.user.id,
        'documents': [office_json(d, handoffs.get(d.id, []), faxes.get(d.id, []), d.id in edited) for d in docs],
        'people': [{'id': u.id, 'name': _display(u), 'role': api._role_of(u)} for u in _staff_users()],
    })


# ---------------------------------------------------------------------------
# Into Office
# ---------------------------------------------------------------------------

def move_to_office(request, doc, review, *, note=None, source=None):
    """Put a document in Office. Call inside a transaction with `doc` and
    `review` locked (`fax_review._locked`).

    From the pool: refused when someone else holds the document; the
    caller's own hold is let go. From a chart, only while the document is in
    review and not yet approved (what "set aside" allowed): it leaves the
    chart with "Removed document" where it was linked, and goes back to the
    team whose pool it came in on. A document already in Office answers
    `already` (and takes the note when one is given).

    Returns (office_row, already, left_patient_id) or a refusal response.
    The caller must `touch_patient_stamp(left_patient_id)` when it is set.
    """
    existing = OfficeDocument.objects.filter(document=doc).first()
    if existing is not None:
        if note:
            existing.note = note
            existing.save(update_fields=['note'])
        return existing, True, None
    if review is not None and review.state == DocumentReview.APPROVED:
        return _refuse('already_approved', 409)

    left = None
    if doc.patient_id is None:
        if doc.team_id is None:
            return _refuse('not_in_pool', 409)
        if fax_review._held_by_other(request.user, doc):
            return _refuse('already_claimed', 409, claimed_by_name=_display(doc.claimed_by))
        chosen = source or OfficeDocument.POOL
        if doc.claimed_by_id is not None:
            doc.claimed_by = None
            doc.claimed_at = None
            doc.save(update_fields=['claimed_by', 'claimed_at'])
    else:
        if review is None or review.state not in (
                DocumentReview.READY, DocumentReview.RETURNED, DocumentReview.FILED):
            return _refuse('not_in_review', 409)
        chosen = source or (OfficeDocument.RETURNED if review.state == DocumentReview.RETURNED
                            else OfficeDocument.QUEUE)
        left = fax_review._take_off_chart(request, doc)
        doc.patient = None
        doc.team_id = review.team_id
        doc.claimed_by = None
        doc.claimed_at = None
        doc.save(update_fields=['patient', 'team', 'claimed_by', 'claimed_at'])

    if review is not None:
        # Back in the pool later, it starts over: nothing decided.
        review.state = DocumentReview.NEW
        review.order_todo = None
        review.returned_note = ''
        review.save()
    office = OfficeDocument.objects.create(
        document=doc, moved_by=request.user, moved_at=timezone.now(), source=chosen, note=note or '')
    # The caller stamps `left` (the chart the document left): the stamp sweep
    # wants the call in the view's own source.
    return office, False, left


def _may_move(user, doc):
    """Who may put a document in Office: anyone who can reach it where it
    is — its pool's team, or its chart."""
    return fax_review._can_reach(user, doc)


def _hand(request, doc, user_ids, note):
    """Hand `doc` to each of `user_ids` (active staff only), reopening a
    hand-off made before. Returns the ids handed to, or a refusal."""
    try:
        wanted = sorted({int(i) for i in (user_ids or [])})
    except (TypeError, ValueError):
        return _refuse('invalid_user_ids', 400)
    if len(wanted) > MAX_HANDOFFS:
        return _refuse('too_many_people', 400)
    people = {u.id: u for u in _staff_users().filter(id__in=wanted)}
    if len(people) != len(wanted):
        return _refuse('person_not_found', 400)
    now = timezone.now()
    for uid in wanted:
        row, created = OfficeHandoff.objects.get_or_create(
            document=doc, user_id=uid,
            defaults={'handed_by': request.user, 'handed_at': now, 'note': note})
        if not created:
            row.handed_by = request.user
            row.handed_at = now
            row.note = note
            row.seen_at = None
            row.done_at = None
            row.save()
    return wanted


@csrf_exempt
@login_required
def mobile_office_move_in(request, document_id):
    """POST {note?, hand_to?: [user ids], hand_note?} -> the document goes to
    Office (see `move_to_office`), handed to those people in the same step."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    note = _note(body.get('note'))
    hand_to = body.get('hand_to') or []
    hand_note = _note(body.get('hand_note')) or note
    if not isinstance(hand_to, list):
        return _refuse('invalid_user_ids', 400)

    with transaction.atomic():
        doc, review = fax_review._locked(document_id)
        if doc is None:
            return _not_found()
        already_here = OfficeDocument.objects.filter(document=doc).exists()
        if not already_here and not _may_move(request.user, doc):
            return _not_found()
        result = move_to_office(request, doc, review, note=note or None)
        if isinstance(result, JsonResponse):
            return result
        office, already, left = result
        if left:
            # Manual stamp: the chart it left is not in the URL.
            touch_patient_stamp(left)
        handed = []
        if hand_to:
            handed = _hand(request, doc, hand_to, hand_note)
            if isinstance(handed, JsonResponse):
                transaction.set_rollback(True)
                return handed
        doc = _office_documents().get(id=doc.id)
        answer = office_json(doc)
    _log('office_moved_in', request, document_id=doc.id, source=office.source, already=already,
         left_patient_id=left, handed_to=handed)
    return JsonResponse({'success': True, 'already': already, 'document': answer})


@csrf_exempt
@login_required
def mobile_office_upload(request):
    """POST multipart {file, client_uuid, document_name?, note?} -> a document
    straight into Office. A retry with the same client_uuid answers the
    document made the first time."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    upload = request.FILES.get('file')
    if upload is None:
        return _refuse('file_required', 400)
    try:
        client_uuid = str(uuid.UUID(str(request.POST.get('client_uuid') or '').strip()))
    except ValueError:
        return _refuse('client_uuid_required', 400)
    name = str(request.POST.get('document_name') or upload.name or 'Document').strip()[:MAX_NAME]
    note = _note(request.POST.get('note'))

    with transaction.atomic():
        doc = Document.objects.filter(client_uuid=client_uuid).first()
        if doc is not None:
            if not OfficeDocument.objects.filter(document=doc).exists():
                # The id was used for something that is not an Office upload.
                return _refuse('client_uuid_reused', 409)
            created = False
        else:
            try:
                with transaction.atomic():
                    doc = Document.objects.create(
                        client_uuid=client_uuid, document=upload, document_name=name, author=request.user,
                        patient=None, team=None, file_size=upload.size, original_file_name=upload.name)
            except IntegrityError:
                doc = Document.objects.get(client_uuid=client_uuid)
                if not OfficeDocument.objects.filter(document=doc).exists():
                    return _refuse('client_uuid_reused', 409)
                created = False
            else:
                OfficeDocument.objects.create(
                    document=doc, moved_by=request.user, moved_at=timezone.now(),
                    source=OfficeDocument.UPLOAD, note=note)
                created = True
        doc = _office_documents().get(id=doc.id)
        answer = office_json(doc)
    _log('office_uploaded', request, document_id=doc.id, created=created)
    return JsonResponse({'success': True, 'created': created, 'document': answer})


@csrf_exempt
@login_required
def mobile_office_from_chart(request):
    """POST {patient_id, document_id, client_uuid, note?, hand_to?, hand_note?}
    -> a copy of a chart document in Office (owner decision 2026-11-18: a
    copy, so the chart keeps its document), marked with the chart it came
    from and handed to those people. The chart says "Copied document to
    Office: <name>". A retry with the same client_uuid answers the first
    copy."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    try:
        patient_id = int(body.get('patient_id'))
        document_id = int(body.get('document_id'))
    except (TypeError, ValueError):
        return _refuse('document_required', 400)
    try:
        client_uuid = str(uuid.UUID(str(body.get('client_uuid') or '').strip()))
    except ValueError:
        return _refuse('client_uuid_required', 400)
    if not api._assert_patient_access(request.user, patient_id):
        return _refuse('patient_not_found', 404)
    source = Document.objects.filter(id=document_id, patient_id=patient_id).select_related('patient').first()
    if source is None:
        return _not_found()
    if not source.document:
        return _refuse('no_file', 409)
    note = _note(body.get('note'))
    hand_to = body.get('hand_to') or []
    hand_note = _note(body.get('hand_note')) or note

    existing = Document.objects.filter(client_uuid=client_uuid).first()
    if existing is not None:
        if not OfficeDocument.objects.filter(document=existing).exists():
            return _refuse('client_uuid_reused', 409)
        return JsonResponse({'success': True, 'already': True,
                             'document': office_json(_office_documents().get(id=existing.id))})
    with source.document.open('rb') as handle:
        data = handle.read()
    from django.core.files.base import ContentFile
    with transaction.atomic():
        copy = Document.objects.create(
            client_uuid=client_uuid, document=ContentFile(data, name=os.path.basename(source.document.name)),
            document_name=source.document_name, author=request.user, patient=None, team=None,
            file_size=len(data), original_file_name=source.original_file_name)
        OfficeDocument.objects.create(
            document=copy, moved_by=request.user, moved_at=timezone.now(), source=OfficeDocument.CHART,
            note=note or ('From %s\u2019s chart' % _display(source.patient)), source_patient_id=patient_id)
        if hand_to:
            handed = _hand(request, copy, hand_to, hand_note)
            if isinstance(handed, JsonResponse):
                transaction.set_rollback(True)
                return handed
        api._emit_document_audit(source, request.user,
                                 'Copied document to Office: %s' % (source.document_name or 'document'))
        # Manual stamp: the patient is in the body, not the URL.
        touch_patient_stamp(patient_id)
        answer = office_json(_office_documents().get(id=copy.id))
    _log('office_copied_from_chart', request, document_id=copy.id, source_document_id=source.id,
         patient_id=patient_id, handed=len(hand_to))
    return JsonResponse({'success': True, 'document': answer})


# ---------------------------------------------------------------------------
# One Office document
# ---------------------------------------------------------------------------

def _locked_office(document_id):
    """The Office document, locked, or None. Call inside a transaction."""
    return Document.objects.select_for_update().filter(id=document_id, office__isnull=False).first()


@csrf_exempt
@login_required
def mobile_office_document(request, document_id):
    """PATCH {document_name} -> rename. DELETE -> delete it permanently."""
    if request.method == 'DELETE':
        return _delete(request, document_id)
    refusal = _gate(request, 'PATCH')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    name = str(body.get('document_name') or '').strip()[:MAX_NAME]
    if not name:
        return _refuse('name_required', 400)
    with transaction.atomic():
        doc = _locked_office(document_id)
        if doc is None:
            return _not_found()
        old = doc.document_name or ''
        if old != name:
            doc.document_name = name
            doc.save(update_fields=['document_name'])
        doc = _office_documents().get(id=doc.id)
        answer = office_json(doc)
    if old != name:
        _log('office_renamed', request, document_id=doc.id)
    return JsonResponse({'success': True, 'document': answer})


def _delete(request, document_id):
    """Permanent: the file, every earlier version and the fax as received
    are removed with the row. Hand-offs go with it; fax records stay, no
    longer naming a document."""
    refusal = _gate(request, 'DELETE')
    if refusal:
        return refusal
    with transaction.atomic():
        doc = _locked_office(document_id)
        if doc is None:
            # Already gone: the same answer as a delete that worked.
            return JsonResponse({'success': True, 'already': True})
        files = document_files(doc)
        snapshot = {'document_id': doc.id, 'source': doc.office.source, 'file_count': len(files)}
        doc.delete()
    missing = delete_stored_files(files)
    if missing:
        LOGGER.warning('%d Office file(s) could not be deleted', missing)
    _log('office_deleted', request, files_not_deleted=missing, **snapshot)
    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_office_to_unassigned(request, document_id):
    """POST {team_id?} -> back to the unassigned pool, the one way to a
    chart. It goes to the team whose pool it came from; a document added
    straight to Office has none, so `team_id` names one of the caller's
    teams. Its hand-offs are removed."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    with transaction.atomic():
        doc = _locked_office(document_id)
        if doc is None:
            return _not_found()
        team_id = doc.team_id
        if team_id is None:
            try:
                team_id = int(body.get('team_id'))
            except (TypeError, ValueError):
                return _refuse('team_required', 400)
            if not api._assert_team_access(request.user, team_id):
                return _refuse('team_not_allowed', 400)
        doc.team_id = team_id
        doc.claimed_by = None
        doc.claimed_at = None
        doc.save(update_fields=['team', 'claimed_by', 'claimed_at'])
        OfficeHandoff.objects.filter(document=doc).delete()
        OfficeDocument.objects.filter(document=doc).delete()
    _log('office_to_unassigned', request, document_id=doc.id, team_id=team_id)
    return JsonResponse({'success': True, 'team_id': team_id})


@csrf_exempt
@login_required
def mobile_office_to_chart(request, document_id):
    """POST {patient_id, document_name?} -> file the document to that
    patient's chart, as the pool's assign does: it leaves Office (hand-offs
    removed), "Renamed document" is written when the name changed, then
    "Added document", and the chart's stamp moves. No review. The caller
    must be able to open the chart (404 `patient_not_found` otherwise)."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    try:
        patient_id = int(body.get('patient_id'))
    except (TypeError, ValueError):
        return _refuse('patient_required', 400)
    if not api._assert_patient_access(request.user, patient_id):
        return _refuse('patient_not_found', 404)
    patient = User.objects.filter(id=patient_id).first()
    if patient is None or api._role_of(patient) != 'patient':
        return _refuse('patient_not_found', 404)
    new_name = str(body.get('document_name') or '').strip()[:MAX_NAME]

    with transaction.atomic():
        doc = _locked_office(document_id)
        if doc is None:
            return _not_found()
        renamed_from = None
        if new_name and new_name != (doc.document_name or ''):
            renamed_from = doc.document_name or ''
            doc.document_name = new_name
        doc.patient = patient
        doc.team = None
        doc.claimed_by = None
        doc.claimed_at = None
        doc.save(update_fields=['patient', 'team', 'claimed_by', 'claimed_at', 'document_name'])
        OfficeHandoff.objects.filter(document=doc).delete()
        OfficeDocument.objects.filter(document=doc).delete()
        # The pool assign's wording, so one query finds every rename and add.
        if renamed_from is not None:
            api._emit_document_audit(
                doc, request.user, f"Renamed document: {renamed_from or 'document'} -> {doc.document_name}")
        api._emit_document_audit(doc, request.user, f"Added document: {doc.document_name or 'document'}")
        # Manual stamp: the patient is in the body, not the URL.
        touch_patient_stamp(patient_id)
    _log('office_to_chart', request, document_id=doc.id, patient_id=patient_id, renamed=renamed_from is not None)
    return JsonResponse({'success': True, 'document_id': doc.id, 'patient_id': patient_id})


# ---------------------------------------------------------------------------
# Hand-offs
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
def mobile_office_hand(request, document_id):
    """POST {user_ids, note} -> hand the document to each of them. Someone it
    was handed to before gets it again: the new note, not seen, not done."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    user_ids = body.get('user_ids')
    if not isinstance(user_ids, list) or not user_ids:
        return _refuse('user_ids_required', 400)
    note = _note(body.get('note'))
    with transaction.atomic():
        doc = _locked_office(document_id)
        if doc is None:
            return _not_found()
        handed = _hand(request, doc, user_ids, note)
        if isinstance(handed, JsonResponse):
            transaction.set_rollback(True)
            return handed
        doc = _office_documents().get(id=doc.id)
        answer = office_json(doc)
    _log('office_handed', request, document_id=doc.id, handed_to=handed)
    return JsonResponse({'success': True, 'document': answer})


def _own_handoff(request, document_id, change):
    with transaction.atomic():
        doc = _locked_office(document_id)
        if doc is None:
            return _not_found()
        row = OfficeHandoff.objects.select_for_update().filter(document=doc, user=request.user).first()
        if row is None:
            return _refuse('not_handed_to_you', 404)
        change(row)
        row.save()
        doc = _office_documents().get(id=doc.id)
        answer = office_json(doc)
    return JsonResponse({'success': True, 'document': answer})


@csrf_exempt
@login_required
def mobile_office_handoff_seen(request, document_id):
    """POST -> the caller has opened the document handed to them."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal

    def seen(row):
        if row.seen_at is None:
            row.seen_at = timezone.now()
    return _own_handoff(request, document_id, seen)


@csrf_exempt
@login_required
def mobile_office_handoff_done(request, document_id):
    """POST {done: true|false} -> the caller's part is finished, or not."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    done = bool(body.get('done', True))

    def mark(row):
        now = timezone.now()
        row.done_at = now if done else None
        if row.seen_at is None:
            row.seen_at = now
    response = _own_handoff(request, document_id, mark)
    if response.status_code == 200:
        _log('office_handoff_done', request, document_id=int(document_id), done=done)
    return response


@csrf_exempt
@login_required
def mobile_office_handoff_remove(request, document_id, user_id):
    """DELETE -> take back the hand-off to that person."""
    refusal = _gate(request, 'DELETE')
    if refusal:
        return refusal
    with transaction.atomic():
        doc = _locked_office(document_id)
        if doc is None:
            return _not_found()
        OfficeHandoff.objects.filter(document=doc, user_id=user_id).delete()
        doc = _office_documents().get(id=doc.id)
        answer = office_json(doc)
    _log('office_handoff_removed', request, document_id=doc.id, user_id=int(user_id))
    return JsonResponse({'success': True, 'document': answer})


# ---------------------------------------------------------------------------
# Editing (the chart editor's routes over Office documents)
# ---------------------------------------------------------------------------

def may_place_office_signature(editor, signer):
    """The editor's own signature, or a physician's the editor works for.
    There is no chart to check the physician against."""
    if signer is None:
        return False
    if signer.id == editor.id:
        return True
    return (api._role_of(signer) == 'physician'
            and PhysicianTeam.objects.filter(physician=signer, member=editor).exists())


def _office_base():
    return Document.objects.filter(office__isnull=False)


@csrf_exempt
@login_required
def mobile_office_edit(request, document_id):
    """POST multipart, the chart edit route's fields, plus `kind=upload` for
    a copy edited outside the app. See `document_edit.save_document_edit`."""
    if not enabled() and api._fax_caller_is_staff(request.user):
        return _refuse('office_disabled', 503)
    return document_edit.save_document_edit(
        request, base=_office_base(), document_id=document_id, may_access=lambda: True,
        signer_allowed=may_place_office_signature, audit=None, log_fields={'office': True},
        allow_upload=True)


@csrf_exempt
@login_required
def mobile_office_restore(request, document_id):
    """POST {edit_id, client_uuid, base_file} -> bring back the version
    before that change."""
    if not enabled() and api._fax_caller_is_staff(request.user):
        return _refuse('office_disabled', 503)
    return document_edit.restore_document_edit(
        request, base=_office_base(), document_id=document_id, may_access=lambda: True,
        audit=None, log_fields={'office': True})


@csrf_exempt
@login_required
def mobile_office_edits(request, document_id):
    """GET -> {edits: every change, oldest first}."""
    refusal = _gate(request, 'GET', write=False)
    if refusal:
        return refusal
    doc = _office_base().filter(id=document_id).first()
    if doc is None:
        return _not_found()
    return document_edit.edits_response(doc)


@csrf_exempt
@login_required
def mobile_office_before_edits(request, document_id):
    """GET -> the document as it was before its first change."""
    refusal = _gate(request, 'GET', write=False)
    if refusal:
        return refusal
    doc = _office_base().filter(id=document_id).first()
    if doc is None:
        return _not_found()
    return document_edit.before_edits_response(doc)


# ---------------------------------------------------------------------------
# Faxing out
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
def mobile_office_fax(request, document_id):
    """POST multipart {file, client_uuid, recipient_id, cover} ->
    {success, transmission}.

    `file` is the PDF to send as the Mac built it: the document, with its
    cover page in front when `cover` is "1" (RingCentral adds none). The
    same rules as a requisition fax: a directory entry only, the client_uuid
    claimed before anything is faxed so a retry never faxes twice, 502
    `fax_send_failed` when RingCentral did not take it (nothing written but
    the failed row; the same id may be sent again), 503 `fax_not_configured`.
    """
    from emr import ringcentral_fax
    from emr.models import FaxRecipient

    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    client_uuid = (request.POST.get('client_uuid') or '').strip()
    if not client_uuid or len(client_uuid) > 36:
        return _refuse('client_uuid_required', 400)
    doc = _office_base().filter(id=document_id).first()
    if doc is None:
        return _not_found()
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

    try:
        with transaction.atomic():
            row = FaxTransmission.objects.create(
                client_uuid=client_uuid, patient=None, document=doc, sender=request.user,
                recipient=recipient, recipient_name=recipient.name, fax_number=recipient.fax_number,
                todo_ids='[]', status=FaxTransmission.SENDING)
    except IntegrityError:
        row = FaxTransmission.objects.get(client_uuid=client_uuid)
        if row.document_id != doc.id:
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

    try:
        sent = ringcentral_fax.send_fax(pdf_bytes, recipient.fax_number, filename='document.pdf')
    except (ringcentral_fax.FaxError, ringcentral_fax.FaxNotConfigured) as error:
        row.status = FaxTransmission.FAILED
        row.error = str(error)[:500]
        row.settled_on = timezone.now()
        row.save()
        _log('office_fax_not_accepted', request, document_id=doc.id, transmission_id=row.id,
             recipient_id=recipient.id, error=row.error)
        # `busy`: RingCentral's per-minute limit, gone in a minute (2026-11-25).
        busy = {'busy': True} if ringcentral_fax.is_busy(error) else {}
        return _refuse('fax_send_failed', 502, detail=row.error, **busy)

    row.rc_message_id = sent['message_id']
    row.rc_status = sent.get('rc_status') or ''
    row.page_count = sent.get('page_count')
    row.status = FaxTransmission.QUEUED
    row.save()
    _log('office_fax_queued', request, document_id=doc.id, transmission_id=row.id, recipient_id=recipient.id,
         fax_number=recipient.fax_number, cover=cover, rc_message_id=row.rc_message_id)
    if sent.get('state') in ('delivered', 'failed'):
        row = api._settle_fax(row.id, sent)
    return JsonResponse({'success': True, 'transmission': api._fax_transmission_json(row)})
