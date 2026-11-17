"""Preparing and approving documents (inbound-fax plan phase 2 and 3,
2026-11-17 — SBR1 PLAN_INBOUND_FAX_2026-11.md).

Staff prepare each fax from the unassigned pool and mark it ready; the
physician whose pool it arrived in approves it with one click. All of the
state is `emr.DocumentReview`; the app keeps none of it.

Rules, each load-bearing:

  * **Ready files the fax to the chart.** It does what assign does (the
    document leaves the pool, "Added document" is written, the chart's stamp
    moves) plus the label, the problem links and the review row. The chart
    shows the document at once, marked not yet reviewed, so staff can answer
    a patient's call about it.
  * **Staff decide, fax by fax** (owner decision 2026-11-17, whatever the
    fax's type): send it to the physician (`ready`), file it to the chart
    themselves with no review (`file`), or park it in "do it later"
    (`later`) to finish another time. Filing is refused for a flagged fax
    (409 `flagged`: turn the flag off first) and when
    `FAX_STAFF_FILE_ENABLED=false` (409 `staff_filing_off`). A parked fax
    stays in the pool, on no chart and out of the physician's queue, until
    someone prepares it.
  * **Only the physician whose pool the fax came in on approves or sends
    back.** Staff, other physicians and admins get 403 `not_approver`.
  * **Approval makes the follow-through, in one transaction**: the fax is
    linked to the order it answers (and the order checked off when asked),
    and the next step becomes an ordinary todo tagged to whoever prepared
    the fax (or to the physician for "I'll call"), with the Activity rows,
    tag rows and `apply_problem_authentication` calls the todo endpoints
    make. Every todo has a problem: the one named in the request, else the
    fax's first problem, else the order's; with none, 400 `problem_required`
    and nothing is written.
  * **Approving twice does nothing the second time.** The row is locked; a
    repeat answers `already: true` and makes no second set of todos.
  * **Set aside takes the document off the chart and out of the pool list**
    and keeps it. Restore returns it to the pool for 30 days; deleting older
    ones is `manage.py purge_set_aside_faxes`, which nothing schedules.
  * **Removing pages never destroys the fax as received.** The Mac cuts the
    pages (the server has no PDF library) and uploads the kept-pages file;
    the first time, the file as received is remembered on the review and is
    never deleted, so it can be served and any page put back.
  * **Refusals are JSON.** A caller with no access gets a JSON 404, so the
    app can tell it from a server without these routes (an HTML 404).

`FAX_REVIEW_ENABLED=false` switches all of it off: the list answers
`enabled: false` and writes answer 503 `fax_review_disabled`.
"""
import datetime
import json
import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from emr.models import (
    Document, DocumentProblem, DocumentReview, DocumentTodo, Label, Problem,
    TaggedToDoOrder, ToDo,
)
from emr.mutation_stamp import touch_patient_stamp
from emr.problem_authentication import apply_problem_authentication
from problems_app.operations import add_problem_activity
from todo_app.operations import add_todo_activity

from . import views as api

LOGGER = logging.getLogger('smallbrain.fax_review')

RESTORE_DAYS = 30
MAX_NOTE = 2000
MAX_NAME = 255
FOLLOW_UP_MAX_DAYS = 730


def _log(event, request, **fields):
    LOGGER.info(json.dumps(dict(
        severity='INFO', message=event, event=event, actor_id=request.user.id,
        serviceContext={'service': 'smallbrain-api'}, **fields)))


def enabled():
    return bool(getattr(settings, 'FAX_REVIEW_ENABLED', True))


def _refuse(error, status, **extra):
    return JsonResponse(dict(success=False, error=error, **extra), status=status)


def _not_found():
    return _refuse('not_found', 404)


def _gate(request, method):
    """The checks every write shares. Returns a response to send, or None."""
    if not api._fax_caller_is_staff(request.user):
        return _not_found()
    if request.method != method:
        return _refuse('%s required' % method, 405)
    if not enabled():
        return _refuse('fax_review_disabled', 503)
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


def _is_approver(user, review):
    """The physician whose pool the fax came in on. A review with no team
    (its physician's account was deleted) can be approved by any physician
    who can see the chart."""
    if api._role_of(user) != 'physician':
        return False
    return review.team_id is None or review.team_id == user.id


def _can_reach(user, doc):
    if doc.patient_id is not None:
        return api._assert_patient_access(user, doc.patient_id)
    if doc.team_id is not None:
        return api._assert_team_access(user, doc.team_id)
    return False


def _held_by_other(user, doc):
    if doc.claimed_by_id is None or doc.claimed_by_id == user.id or doc.claimed_at is None:
        return False
    cutoff = timezone.now() - datetime.timedelta(seconds=api._UNASSIGNED_CLAIM_TTL_SECONDS)
    return doc.claimed_at >= cutoff


def _locked(document_id):
    """(document, review-or-None), both locked. Call inside a transaction."""
    doc = Document.objects.select_for_update().filter(id=document_id).first()
    if doc is None:
        return None, None
    review = DocumentReview.objects.select_for_update().filter(document=doc).first()
    return doc, review


def _removed_pages(review):
    try:
        pages = json.loads(review.removed_pages or '[]')
    except ValueError:
        pages = []
    return pages if isinstance(pages, list) else []


def _changes(review):
    try:
        changes = json.loads(review.changes or '[]')
    except ValueError:
        changes = []
    return changes if isinstance(changes, list) else []


# ---------------------------------------------------------------------------
# What the app is told
# ---------------------------------------------------------------------------

def _patient_json(patient):
    if patient is None:
        return None
    dob = None
    try:
        if patient.profile.date_of_birth:
            dob = patient.profile.date_of_birth.isoformat()
    except Exception:
        dob = None
    return {'id': patient.id, 'name': _display(patient), 'first_name': patient.first_name,
            'last_name': patient.last_name, 'date_of_birth': dob}


def _todo_json(todo):
    if todo is None:
        return None
    return {'id': todo.id, 'title': todo.todo or '', 'problem_id': todo.problem_id,
            'problem_name': todo.problem.problem_name if todo.problem_id else None,
            'accomplished': todo.accomplished, 'due_date': _iso(todo.due_date)}


def review_json(review, detail=False):
    """One review. `detail` adds what the approval screen needs to edit it:
    the chart's open todos and its problems."""
    doc = review.document
    removed = _removed_pages(review)
    row = {
        'document_id': doc.id,
        'state': review.state,
        'document_name': doc.document_name or '',
        'file_size': api._document_file_size(doc),
        'team_id': review.team_id,
        'patient': _patient_json(doc.patient) if doc.patient_id else None,
        'labels': [l.name or '' for l in doc.labels.all()],
        'problem_ids': list(DocumentProblem.objects.filter(
            document=doc, problem_id__isnull=False).values_list('problem_id', flat=True)),
        'note': review.note,
        'flagged': review.flagged,
        'order_todo': _todo_json(review.order_todo) if review.order_todo_id else None,
        'prepared_by_id': review.prepared_by_id,
        'prepared_by_name': _display(review.prepared_by) if review.prepared_by_id else '',
        'prepared_at': _iso(review.prepared_at),
        'returned_note': review.returned_note,
        'returned_by_name': _display(review.returned_by) if review.returned_by_id else '',
        'returned_at': _iso(review.returned_at),
        'approved_by_name': _display(review.approved_by) if review.approved_by_id else '',
        'approved_at': _iso(review.approved_at),
        'next_step': review.next_step or None,
        'message': review.message,
        'changed_fields': [c.get('field') for c in _changes(review) if isinstance(c, dict)],
        'set_aside_by_name': _display(review.set_aside_by) if review.set_aside_by_id else '',
        'set_aside_at': _iso(review.set_aside_at),
        'later_by_name': _display(review.later_by) if review.later_by_id else '',
        'later_at': _iso(review.later_at),
        'removed_pages': removed,
        'has_original': bool(review.original_file),
        **api._inbound_fax_fields(doc),
    }
    if detail and doc.patient_id:
        row['open_orders'] = [
            _todo_json(t) for t in
            ToDo.objects.filter(patient_id=doc.patient_id, accomplished=False)
            .select_related('problem').order_by('-id')[:200]]
        row['problems'] = [
            {'id': p.id, 'name': p.problem_name or '', 'is_active': p.is_active}
            for p in Problem.objects.filter(patient_id=doc.patient_id).order_by('-is_active', 'problem_name')]
    return row


def _reviews(state):
    return DocumentReview.objects.filter(state=state).select_related(
        'document', 'document__patient', 'document__patient__profile', 'document__inbound_fax',
        'order_todo', 'order_todo__problem', 'prepared_by', 'returned_by', 'approved_by',
        'set_aside_by', 'later_by').prefetch_related('document__labels')


def _visible(queryset, user):
    """The reviews this login may see: its teams' pools, and for a document
    on a chart, only a chart it can open."""
    teams = api._user_team_ids(user)
    if teams is not None:
        if not teams:
            return []
        queryset = queryset.filter(team_id__in=teams)
    patients = api._accessible_patient_ids(user)
    rows = []
    allowed = None if patients is None else set(patients)
    for review in queryset:
        pid = review.document.patient_id
        if pid is not None and allowed is not None and pid not in allowed:
            continue
        rows.append(review)
    return rows


@csrf_exempt
@login_required
def mobile_fax_reviews(request):
    """GET -> the review lists for this login.

      queue      — prepared, waiting for the physician: flagged first, then
                   the longest waiting. Staff see it too, read-only.
      returned   — sent back to staff with a note
      later      — parked by staff to finish later, the longest parked
                   first; still in the pool
      set_aside  — set aside in the last 30 days (restorable)
      week       — approvals in the last 7 days and how many the physician
                   changed

    `enabled: false` (and nothing else) when the feature is switched off.
    `is_approver` says whether this login is a physician, the only role that
    approves; each row's own `team_id` says whose queue it is in.
    """
    if not api._fax_caller_is_staff(request.user):
        return _not_found()
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not enabled():
        return JsonResponse({'success': True, 'enabled': False})

    user = request.user
    queue = _visible(_reviews(DocumentReview.READY), user)
    queue.sort(key=lambda r: (0 if r.flagged else 1, r.prepared_at or r.created_on))
    returned = _visible(_reviews(DocumentReview.RETURNED).order_by('-returned_at'), user)
    later = _visible(_reviews(DocumentReview.LATER).order_by('later_at', 'id'), user)
    cutoff = timezone.now() - datetime.timedelta(days=RESTORE_DAYS)
    set_aside = _visible(
        _reviews(DocumentReview.SET_ASIDE).filter(set_aside_at__gte=cutoff).order_by('-set_aside_at'), user)

    week = timezone.now() - datetime.timedelta(days=7)
    recent = DocumentReview.objects.filter(
        state=DocumentReview.APPROVED, approved_by=user, approved_at__gte=week)
    approver = api._role_of(user) == 'physician'
    return JsonResponse({
        'success': True,
        'enabled': True,
        'is_approver': approver,
        # The chart's orders and problems ride along only where they are
        # edited: the physician's queue, and what was sent back to staff.
        # Staff Macs ask every 30 s for the counts.
        'queue': [review_json(r, detail=approver) for r in queue],
        'returned': [review_json(r, detail=True) for r in returned],
        'later': [review_json(r) for r in later],
        'set_aside': [review_json(r) for r in set_aside],
        'week': {'approved': recent.count(), 'changed': recent.exclude(changes='[]').count()},
        'restore_days': RESTORE_DAYS,
    })


@csrf_exempt
@login_required
def mobile_patient_document_reviews(request, patient_id):
    """GET -> the review of each of this chart's documents that has one, for
    the Docs tab's mark ("Not yet reviewed" / "Reviewed by …" / "Filed by …",
    the last for a fax staff filed with no review). Read-only."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not api._fax_caller_is_staff(request.user) or not api._assert_patient_access(request.user, patient_id):
        return _not_found()
    if not enabled():
        return JsonResponse({'success': True, 'enabled': False, 'reviews': []})
    rows = DocumentReview.objects.filter(document__patient_id=patient_id).exclude(
        state__in=[DocumentReview.NEW, DocumentReview.SET_ASIDE]).select_related(
        'prepared_by', 'approved_by', 'returned_by')
    return JsonResponse({'success': True, 'enabled': True, 'reviews': [{
        'document_id': r.document_id,
        'state': r.state,
        'flagged': r.flagged,
        'prepared_by_name': _display(r.prepared_by) if r.prepared_by_id else '',
        'prepared_at': _iso(r.prepared_at),
        'approved_by_name': _display(r.approved_by) if r.approved_by_id else '',
        'approved_at': _iso(r.approved_at),
        'next_step': r.next_step or None,
        'returned_note': r.returned_note,
        'removed_page_count': len(_removed_pages(r)),
        'has_original': bool(r.original_file),
    } for r in rows]})


@csrf_exempt
@login_required
def mobile_fax_review(request, document_id):
    """GET -> {review: one document's review, or null when it has none,
    staff_may_file: whether staff may file it without review}.

    The prepare sheet asks before it shows a pool fax, because the pool list
    does not say whether pages were removed on another Mac: without the list
    of removed pages a Mac would number pages from its own, possibly
    outdated, copy of the file. The same answer tells it whether to offer
    "File to chart". Read-only."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not api._fax_caller_is_staff(request.user):
        return _not_found()
    doc = Document.objects.filter(id=document_id).select_related('patient', 'inbound_fax').first()
    if doc is None or not _can_reach(request.user, doc):
        return _not_found()
    if not enabled():
        return JsonResponse({'success': True, 'enabled': False, 'review': None, 'staff_may_file': False})
    review = DocumentReview.objects.filter(document=doc).select_related(
        'order_todo', 'order_todo__problem', 'prepared_by', 'returned_by', 'approved_by', 'set_aside_by',
        'later_by').first()
    return JsonResponse({'success': True, 'enabled': True,
                         'review': review_json(review, detail=True) if review else None,
                         'staff_may_file': staff_may_file()})


# ---------------------------------------------------------------------------
# Changing a document the way the existing endpoints do
# ---------------------------------------------------------------------------

def _rename(request, doc, name):
    name = (name or '').strip()[:MAX_NAME]
    old = doc.document_name or ''
    if not name or name == old:
        return False
    doc.document_name = name
    doc.save(update_fields=['document_name'])
    if doc.patient_id:
        api._emit_document_audit(doc, request.user, f"Renamed document: {old or 'document'} -> {name}")
    return True


# The document-type labels. A document carries one of them; "screening" and
# any ad-hoc label sit beside it and are never touched here.
TYPE_LABELS = ('laboratory', 'imaging', 'procedure', 'correspondence', 'referral', 'medication')


def staff_may_file():
    """Whether staff may file a fax to the chart without the physician's
    approval: on unless `FAX_STAFF_FILE_ENABLED=false`."""
    return bool(getattr(settings, 'FAX_STAFF_FILE_ENABLED', True))


def _set_label(request, doc, name):
    """The document's type label is exactly this one afterwards: another type
    label it carried is taken off, other labels ("screening") stay. An empty
    name changes nothing. Same canonical-row rule and audit wording as
    `mobile_document_label`. Returns whether anything changed."""
    name = (name or '').strip()
    if not name:
        return False
    current = list(doc.labels.all())
    label = Label.objects.filter(name__iexact=name).order_by('-is_all', 'id').first()
    if label is None:
        label = Label.objects.create(name=name, css_class='', author=request.user)
    changed = False
    for other in current:
        if other.id != label.id and (other.name or '').lower() in TYPE_LABELS:
            doc.labels.remove(other)
            add_problem_activity(None, request.user, f"Removed label: {other.name or 'label'}")
            changed = True
    if not any(other.id == label.id for other in current):
        doc.labels.add(label)
        add_problem_activity(None, request.user, f"Added label: {label.name or 'label'}")
        changed = True
    return changed


def _set_problems(request, doc, problem_ids):
    """The document is linked to exactly these problems of its chart
    afterwards. Ids that are not this chart's problems are ignored."""
    wanted = set(Problem.objects.filter(
        patient_id=doc.patient_id, id__in=[i for i in problem_ids if isinstance(i, int)]
    ).values_list('id', flat=True))
    links = {l.problem_id: l for l in DocumentProblem.objects.filter(document=doc).select_related('problem')}
    name = doc.document_name or 'document'
    changed = False
    for problem_id, link in links.items():
        if problem_id not in wanted:
            problem = link.problem
            link.delete()
            add_problem_activity(problem, request.user, f"Unlinked document: {name}")
            apply_problem_authentication(request, problem)
            changed = True
    for problem in Problem.objects.filter(id__in=wanted - set(links)):
        DocumentProblem.objects.create(document=doc, problem=problem, author=request.user)
        add_problem_activity(problem, request.user, f"Linked document: {name}")
        apply_problem_authentication(request, problem)
        changed = True
    return changed


def _take_off_chart(request, doc):
    """Unlink the document from its chart's problems and todos and write
    "Removed document" where each link was. Returns the patient id it left."""
    patient_id = doc.patient_id
    name = doc.document_name or 'document'
    message = f"Removed document: {name}"
    problem_links = list(DocumentProblem.objects.filter(document=doc).select_related('problem'))
    todo_links = list(DocumentTodo.objects.filter(document=doc).select_related('todo'))
    if problem_links:
        for link in problem_links:
            add_problem_activity(link.problem, request.user, message)
    else:
        add_problem_activity(None, request.user, message)
    for link in todo_links:
        add_todo_activity(link.todo, request.user, message)
    DocumentProblem.objects.filter(document=doc).delete()
    DocumentTodo.objects.filter(document=doc).delete()
    return patient_id


def _link_todo(request, doc, todo):
    """`mobile_document_todo_link`'s POST, for a todo of the document's chart."""
    link, created = DocumentTodo.objects.get_or_create(
        document=doc, todo=todo, defaults={'author': request.user})
    if created:
        name = doc.document_name or 'document'
        add_problem_activity(todo.problem if todo.problem_id else None, request.user,
                             f"Linked document to todo: {name}")
        add_todo_activity(todo, request.user, f"Linked document: {name}")
    return created


def _tag(request, todo, member):
    """`mobile_add_todo_member`: tagged as New, with its Activity row."""
    if member is None:
        return
    tag, created = TaggedToDoOrder.objects.get_or_create(todo=todo, user=member)
    if created:
        add_todo_activity(todo, request.user, f"Tagged {_display(member)}")
    elif tag.status != 0:
        tag.status = 0
        tag.save(update_fields=['status'])


def _create_todo(request, patient, problem, title, tagged=None, due=None, label_name=None, doc=None):
    """`mobile_create_todo`, plus the tag, the label and the link to the fax
    that the approval asks for."""
    todo = ToDo(todo=title, patient=patient, user=request.user, problem=problem, due_date=due)
    todo.save()
    add_todo_activity(todo, request.user, f"Added todo: {title}")
    add_problem_activity(problem, request.user, f"Added todo: {title}")
    apply_problem_authentication(request, problem, non_physician_clears=True)
    if label_name:
        label = Label.objects.filter(name__iexact=label_name).order_by('-is_all', 'id').first()
        if label is not None:
            todo.labels.add(label)
    _tag(request, todo, tagged)
    if doc is not None:
        _link_todo(request, doc, todo)
    return todo


def _check_off(request, todo):
    """`mobile_update_todo` with accomplished: true."""
    if todo.accomplished:
        return False
    todo.accomplished = True
    todo.save()
    add_todo_activity(todo, request.user, "Updated status to accomplished")
    if todo.problem_id:
        add_problem_activity(todo.problem, request.user, f'Todo "{todo.todo}" marked accomplished')
    apply_problem_authentication(request, todo.problem, non_physician_clears=True)
    return True


def _order_todo(patient_id, raw):
    """The chart's todo with this id, or None."""
    try:
        todo_id = int(raw)
    except (TypeError, ValueError):
        return None
    return ToDo.objects.filter(id=todo_id, patient_id=patient_id).select_related('problem').first()


def _assign_from_pool(request, doc, patient, body):
    """Assign: the same row change and audit as
    mobile_unassigned_document_assign, with the name staff chose and the page
    text their Mac read. Clears `Document.team`, so a caller that needs the
    pool's team reads it first."""
    old_name = doc.document_name or ''
    new_name = (body.get('document_name') or '').strip()[:MAX_NAME] or old_name
    doc.document_name = new_name
    fields = ['patient', 'team', 'claimed_by', 'claimed_at', 'document_name']
    text = body.get('extracted_text')
    if isinstance(text, str) and (text or not doc.extracted_text):
        doc.extracted_text = text
        doc.extracted_text_at = timezone.now()
        try:
            version = body.get('extracted_text_version')
            doc.extracted_text_version = int(version) if version not in (None, '') else None
        except (TypeError, ValueError):
            doc.extracted_text_version = None
        fields += ['extracted_text', 'extracted_text_at', 'extracted_text_version']
    doc.patient = patient
    doc.team = None
    doc.claimed_by = None
    doc.claimed_at = None
    doc.save(update_fields=fields)
    if new_name != old_name:
        api._emit_document_audit(
            doc, request.user, f"Renamed document: {old_name or 'document'} -> {new_name}")
    api._emit_document_audit(doc, request.user, f"Added document: {new_name or 'document'}")


# ---------------------------------------------------------------------------
# Staff: ready, file, set aside, restore
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
def mobile_fax_review_ready(request, document_id):
    """POST {patient_id, document_name?, label?, problem_ids?, order_todo_id?,
    note?, flagged?, extracted_text?, extracted_text_version?} -> the fax is
    filed to the chart and waits for the physician.

    From the pool this is assign plus the prepared fields. For a fax the
    physician sent back (or one still waiting) it updates what was prepared;
    a different `patient_id` moves the document to that chart, with "Removed
    document" on the chart it leaves and "Added document" on the one it
    joins. An approved fax is refused (409 `already_approved`).
    """
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    target_id = body.get('patient_id')
    if not target_id or not api._assert_patient_access(request.user, target_id):
        return _refuse('patient_not_found', 404)
    patient = User.objects.filter(id=target_id).first()
    if patient is None:
        return _refuse('patient_not_found', 404)

    stamped = set()
    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or not _can_reach(request.user, doc):
            return _not_found()
        if review is not None and review.state == DocumentReview.APPROVED:
            return _refuse('already_approved', 409)
        if review is not None and review.state == DocumentReview.SET_ASIDE:
            return _refuse('set_aside', 409)
        from_pool = doc.patient_id is None
        if from_pool and _held_by_other(request.user, doc):
            return _refuse('already_claimed', 409, claimed_by_name=_display(doc.claimed_by))
        if not from_pool and review is None:
            # A chart document nobody prepared was filed the old way.
            return _refuse('not_in_review', 409)
        if review is None:
            review = DocumentReview(document=doc)
        if from_pool:
            review.team_id = doc.team_id

        if from_pool:
            _assign_from_pool(request, doc, patient, body)
        else:
            if doc.patient_id != patient.id:
                stamped.add(_take_off_chart(request, doc))
                doc.patient = patient
                doc.save(update_fields=['patient'])
                api._emit_document_audit(
                    doc, request.user, f"Added document: {doc.document_name or 'document'}")
                review.order_todo = None
            _rename(request, doc, body.get('document_name'))
        stamped.add(patient.id)

        _set_label(request, doc, body.get('label'))
        if isinstance(body.get('problem_ids'), list):
            _set_problems(request, doc, body['problem_ids'])
        if 'order_todo_id' in body:
            review.order_todo = _order_todo(patient.id, body.get('order_todo_id'))
        if 'note' in body:
            review.note = str(body.get('note') or '')[:MAX_NOTE]
        if 'flagged' in body:
            review.flagged = bool(body.get('flagged'))
        review.state = DocumentReview.READY
        review.prepared_by = request.user
        review.prepared_at = timezone.now()
        review.save()
        for pid in stamped:
            # Manual stamp: the chart is named in the body, not the URL.
            touch_patient_stamp(pid)
        answer = review_json(review, detail=True)

    _log('fax_review_ready', request, document_id=doc.id, patient_id=patient.id, from_pool=from_pool)
    return JsonResponse({'success': True, 'review': answer})


@csrf_exempt
@login_required
def mobile_fax_review_file(request, document_id):
    """POST {patient_id, label, document_name?, problem_ids?, order_todo_id?,
    note?, extracted_text?, extracted_text_version?} -> the fax is filed to
    the chart with no review (owner decision 2026-11-17: staff decide, fax
    by fax, whatever its type).

    Only a fax still in the pool (new or parked), with a label, never a
    flagged one, and only while `FAX_STAFF_FILE_ENABLED`: otherwise 400
    `label_required` or 409 (`flagged`, `staff_filing_off`, `not_in_pool`,
    `set_aside`) and nothing changes. It is assign plus the prepared fields;
    because no approval follows, the order the fax answers is linked now
    (never checked off). The review row is kept in state `filed`, so the
    chart says who filed it and the physician's queue never shows it.
    """
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    if not staff_may_file():
        return _refuse('staff_filing_off', 409)
    label = str(body.get('label') or '').strip()
    if not label:
        return _refuse('label_required', 400)
    if bool(body.get('flagged')):
        return _refuse('flagged', 409)
    target_id = body.get('patient_id')
    if not target_id or not api._assert_patient_access(request.user, target_id):
        return _refuse('patient_not_found', 404)
    patient = User.objects.filter(id=target_id).first()
    if patient is None:
        return _refuse('patient_not_found', 404)

    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or not _can_reach(request.user, doc):
            return _not_found()
        if review is not None and review.state == DocumentReview.SET_ASIDE:
            return _refuse('set_aside', 409)
        if doc.patient_id is not None:
            return _refuse('not_in_pool', 409, state=review.state if review else None)
        if _held_by_other(request.user, doc):
            return _refuse('already_claimed', 409, claimed_by_name=_display(doc.claimed_by))
        if review is None:
            review = DocumentReview(document=doc)
        review.team_id = doc.team_id
        _assign_from_pool(request, doc, patient, body)
        _set_label(request, doc, label)
        if isinstance(body.get('problem_ids'), list):
            _set_problems(request, doc, body['problem_ids'])
        order = _order_todo(patient.id, body.get('order_todo_id'))
        if order is not None:
            _link_todo(request, doc, order)
        review.order_todo = order
        review.note = str(body.get('note') or '')[:MAX_NOTE]
        review.flagged = False
        review.state = DocumentReview.FILED
        review.prepared_by = request.user
        review.prepared_at = timezone.now()
        review.save()
        # Manual stamp: the chart is named in the body, not the URL.
        touch_patient_stamp(patient.id)
        answer = review_json(review)

    _log('fax_review_filed', request, document_id=doc.id, patient_id=patient.id, label=label.lower())
    return JsonResponse({'success': True, 'review': answer})


@csrf_exempt
@login_required
def mobile_fax_review_later(request, document_id):
    """POST {note?} -> "do it later": staff park a pool fax to finish another
    time (owner decision 2026-11-17).

    The fax stays in the pool, on no chart and out of the physician's queue;
    the lists show it under `later` with who parked it and when. Preparing
    it later (ready, file, set aside) moves it on. Only from the pool; a fax
    someone else holds is refused, and the caller's own hold is let go so
    anyone can pick it up. Parking it again replaces the note.
    """
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or not _can_reach(request.user, doc):
            return _not_found()
        if review is not None and review.state == DocumentReview.SET_ASIDE:
            return _refuse('set_aside', 409)
        if doc.patient_id is not None:
            return _refuse('not_in_pool', 409, state=review.state if review else None)
        if _held_by_other(request.user, doc):
            return _refuse('already_claimed', 409, claimed_by_name=_display(doc.claimed_by))
        if review is None:
            review = DocumentReview(document=doc, team_id=doc.team_id)
        if doc.claimed_by_id == request.user.id:
            doc.claimed_by = None
            doc.claimed_at = None
            doc.save(update_fields=['claimed_by', 'claimed_at'])
        review.state = DocumentReview.LATER
        review.later_by = request.user
        review.later_at = timezone.now()
        if 'note' in body:
            review.note = str(body.get('note') or '')[:MAX_NOTE]
        review.save()
        answer = review_json(review)
    _log('fax_review_later', request, document_id=doc.id)
    return JsonResponse({'success': True, 'review': answer})


@csrf_exempt
@login_required
def mobile_fax_review_set_aside(request, document_id):
    """POST -> not for a chart. One button, no reason asked.

    From the pool: any member of the pool's team (unless someone else holds
    the claim). From a chart, while it waits or was sent back: the approver
    or anyone who can open the chart; the document leaves the chart with
    "Removed document" where it was linked. An approved fax is refused.
    """
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or not _can_reach(request.user, doc):
            return _not_found()
        if review is not None and review.state == DocumentReview.APPROVED:
            return _refuse('already_approved', 409)
        if review is not None and review.state == DocumentReview.SET_ASIDE:
            return JsonResponse({'success': True, 'already': True, 'review': review_json(review)})
        if doc.patient_id is None and _held_by_other(request.user, doc):
            return _refuse('already_claimed', 409, claimed_by_name=_display(doc.claimed_by))
        if doc.patient_id is not None and review is None:
            return _refuse('not_in_review', 409)
        if review is None:
            review = DocumentReview(document=doc, team_id=doc.team_id)
        left = None
        if doc.patient_id is not None:
            left = _take_off_chart(request, doc)
            doc.patient = None
            doc.team_id = review.team_id
            doc.claimed_by = None
            doc.claimed_at = None
            doc.save(update_fields=['patient', 'team', 'claimed_by', 'claimed_at'])
            review.order_todo = None
        review.state = DocumentReview.SET_ASIDE
        review.set_aside_by = request.user
        review.set_aside_at = timezone.now()
        review.save()
        if left:
            # Manual stamp: the chart it left is not in the URL.
            touch_patient_stamp(left)
        answer = review_json(review)
    _log('fax_review_set_aside', request, document_id=doc.id, left_patient_id=left)
    return JsonResponse({'success': True, 'review': answer})


@csrf_exempt
@login_required
def mobile_fax_review_restore(request, document_id):
    """POST -> a set-aside fax goes back to the pool, within 30 days."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or review is None or not _can_reach(request.user, doc):
            return _not_found()
        if review.state != DocumentReview.SET_ASIDE:
            return JsonResponse({'success': True, 'already': True})
        cutoff = timezone.now() - datetime.timedelta(days=RESTORE_DAYS)
        if review.set_aside_at is not None and review.set_aside_at < cutoff:
            return _refuse('too_old', 409)
        if doc.team_id is None:
            return _refuse('no_team', 409)
        review.state = DocumentReview.NEW
        review.set_aside_by = None
        review.set_aside_at = None
        review.returned_note = ''
        review.save()
    _log('fax_review_restored', request, document_id=doc.id)
    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# The physician: send back, approve
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
def mobile_fax_review_send_back(request, document_id):
    """POST {note?} -> back to staff with a note. Approver only. The document
    stays on the chart, still marked not yet reviewed."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or review is None or not _can_reach(request.user, doc):
            return _not_found()
        if not _is_approver(request.user, review):
            return _refuse('not_approver', 403)
        if review.state == DocumentReview.RETURNED:
            return JsonResponse({'success': True, 'already': True})
        if review.state != DocumentReview.READY:
            return _refuse('not_waiting', 409, state=review.state)
        review.state = DocumentReview.RETURNED
        review.returned_by = request.user
        review.returned_at = timezone.now()
        review.returned_note = str(body.get('note') or '').strip()[:MAX_NOTE] or 'Please check this one'
        review.save()
        # Manual stamp: the chart is not in the URL.
        touch_patient_stamp(doc.patient_id)
    _log('fax_review_sent_back', request, document_id=doc.id, patient_id=doc.patient_id)
    return JsonResponse({'success': True})


def _call_title(step, patient_name, doc_name, message):
    if step in (DocumentReview.STAFF_CALL, DocumentReview.PHYSICIAN_CALL):
        return f"Call {patient_name}: {message}" if message else f"Call {patient_name} about {doc_name}"
    if step == DocumentReview.TELL_PATIENT:
        return f"Tell {patient_name} the {doc_name} is fine" + (f": {message}" if message else '')
    return None


@csrf_exempt
@login_required
def mobile_fax_review_approve(request, document_id):
    """POST {next_step, message?, mark_order_done?, problem_id?,
    follow_up_title?, follow_up_days?, edits?: {document_name?, label?,
    problem_ids?, order_todo_id?}} -> reviewed. Approver only.

    `next_step` is one of staff_call, physician_call, tell_patient,
    nothing_to_tell (the physician's keys 1–4; there is no letter step). Every
    step but nothing_to_tell makes a todo: the call, or telling the patient,
    tagged to whoever prepared the fax, or to the physician for
    physician_call. A `follow_up_title` with
    `follow_up_days` makes the follow-up order, due that many days out,
    tagged to the preparer. The fax is linked to its order either way, and
    the order is checked off when `mark_order_done`.

    `edits` are the physician's corrections to what staff prepared; each
    field that really changed is recorded on the review.
    """
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    step = body.get('next_step')
    if step not in DocumentReview.NEXT_STEPS:
        return _refuse('next_step_required', 400)
    edits = body.get('edits') if isinstance(body.get('edits'), dict) else {}
    message = ' '.join(str(body.get('message') or '').split())[:500]
    follow_title = ' '.join(str(body.get('follow_up_title') or '').split())[:255]
    follow_days = body.get('follow_up_days')
    if follow_title:
        if not isinstance(follow_days, int) or isinstance(follow_days, bool) \
                or not 1 <= follow_days <= FOLLOW_UP_MAX_DAYS:
            return _refuse('follow_up_days_required', 400)

    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or review is None or doc.patient_id is None or not _can_reach(request.user, doc):
            return _not_found()
        if not _is_approver(request.user, review):
            return _refuse('not_approver', 403)
        if review.state == DocumentReview.APPROVED:
            return JsonResponse({'success': True, 'already': True, 'todo_ids': [],
                                 'patient_id': doc.patient_id, 'review': review_json(review)})
        if review.state != DocumentReview.READY:
            return _refuse('not_waiting', 409, state=review.state)
        patient = doc.patient

        # The physician's corrections, each recorded only if it changed.
        changes = _changes(review)
        if 'document_name' in edits:
            old = doc.document_name or ''
            if _rename(request, doc, edits.get('document_name')):
                changes.append({'field': 'document_name', 'from': old, 'to': doc.document_name})
        if 'label' in edits:
            old = [l.name or '' for l in doc.labels.all()]
            if _set_label(request, doc, edits.get('label')):
                changes.append({'field': 'label', 'from': old, 'to': [l.name or '' for l in doc.labels.all()]})
        if isinstance(edits.get('problem_ids'), list):
            old = sorted(DocumentProblem.objects.filter(document=doc).values_list('problem_id', flat=True))
            if _set_problems(request, doc, edits['problem_ids']):
                new = sorted(DocumentProblem.objects.filter(document=doc).values_list('problem_id', flat=True))
                changes.append({'field': 'problems', 'from': old, 'to': new})
        if 'order_todo_id' in edits:
            old = review.order_todo_id
            review.order_todo = _order_todo(patient.id, edits.get('order_todo_id'))
            if review.order_todo_id != old:
                changes.append({'field': 'order', 'from': old, 'to': review.order_todo_id})
        if any(entry.get('by') == request.user.id for entry in _removed_pages(review)
               if isinstance(entry, dict)) and not any(c.get('field') == 'pages' for c in changes):
            changes.append({'field': 'pages'})

        order = review.order_todo if review.order_todo_id else None
        if order is not None and order.patient_id != patient.id:
            order = None

        # Every todo has a problem.
        call_title = _call_title(step, _display(patient), doc.document_name or 'document', message)
        problem = None
        if call_title or follow_title:
            if body.get('problem_id'):
                problem = Problem.objects.filter(id=body.get('problem_id'), patient_id=patient.id).first() \
                    if isinstance(body.get('problem_id'), int) else None
                if problem is None:
                    transaction.set_rollback(True)
                    return _refuse('problem_not_found', 404)
            if problem is None:
                link = DocumentProblem.objects.filter(document=doc).select_related('problem').order_by('id').first()
                problem = link.problem if link is not None else None
            if problem is None and order is not None and order.problem_id:
                problem = order.problem
            if problem is None:
                transaction.set_rollback(True)
                return _refuse('problem_required', 400)

        preparer = review.prepared_by if review.prepared_by_id else request.user
        todo_ids = []
        if order is not None:
            _link_todo(request, doc, order)
            if bool(body.get('mark_order_done')):
                review.order_marked_done = _check_off(request, order)
        if call_title:
            tagged = request.user if step == DocumentReview.PHYSICIAN_CALL else preparer
            todo_ids.append(_create_todo(request, patient, problem, call_title, tagged=tagged, doc=doc).id)
        if follow_title:
            names = {(l.name or '').lower() for l in doc.labels.all()}
            label = 'Imaging' if 'imaging' in names else ('Laboratory' if 'laboratory' in names else None)
            due = timezone.now() + datetime.timedelta(days=follow_days)
            todo_ids.append(_create_todo(
                request, patient, problem, follow_title, tagged=preparer, due=due, label_name=label).id)

        review.state = DocumentReview.APPROVED
        review.approved_by = request.user
        review.approved_at = timezone.now()
        review.next_step = step
        review.message = message
        review.changes = json.dumps(changes)
        review.save()
        add_problem_activity(None, request.user, f"Reviewed document: {doc.document_name or 'document'}")
        # Manual stamp: the chart is not in the URL.
        touch_patient_stamp(patient.id)
        answer = review_json(review)

    _log('fax_review_approved', request, document_id=doc.id, patient_id=patient.id, next_step=step,
         todos=len(todo_ids), changed=[c.get('field') for c in changes])
    return JsonResponse({'success': True, 'review': answer, 'todo_ids': todo_ids,
                         'patient_id': patient.id})


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
def mobile_fax_review_pages(request, document_id):
    """POST multipart {file?, removed_pages, original_page_count?, reasons?}
    -> the document's file becomes the kept pages.

    `removed_pages` is the whole list of pages now out of the fax, numbered
    in the file as received (JSON, e.g. [1, 4]); `file` is the PDF without
    them, cut on the Mac. An empty list puts every page back: no file is
    needed and the document's file is the one that arrived. `reasons` may
    name why a page went ({"1": "Cover sheet"}).

    The file as received is never deleted. Who removed each page and when is
    kept; a page still out keeps its first entry. Refused once the fax is
    approved or set aside. The document's text is cleared so the next Mac to
    read it indexes the kept pages.
    """
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    try:
        wanted = json.loads(request.POST.get('removed_pages') or '')
        reasons = json.loads(request.POST.get('reasons') or '{}')
    except ValueError:
        return _refuse('removed_pages_required', 400)
    if not isinstance(wanted, list) or not all(
            isinstance(p, int) and not isinstance(p, bool) and p >= 1 for p in wanted) \
            or len(set(wanted)) != len(wanted):
        return _refuse('removed_pages_required', 400)
    if not isinstance(reasons, dict):
        reasons = {}
    try:
        page_count = int(request.POST.get('original_page_count') or 0)
    except ValueError:
        page_count = 0
    if page_count and (len(wanted) >= page_count or max(wanted, default=0) > page_count):
        return _refuse('last_page', 400)
    upload = request.FILES.get('file')
    if wanted:
        if upload is None:
            return _refuse('file_required', 400)
        head = upload.read(5)
        upload.seek(0)
        if not head.startswith(b'%PDF'):
            return _refuse('not_a_pdf', 400)

    with transaction.atomic():
        doc, review = _locked(document_id)
        if doc is None or not _can_reach(request.user, doc):
            return _not_found()
        if review is not None and review.state in (DocumentReview.APPROVED, DocumentReview.SET_ASIDE):
            return _refuse('already_approved' if review.state == DocumentReview.APPROVED else 'set_aside', 409)
        if doc.patient_id is None and _held_by_other(request.user, doc):
            return _refuse('already_claimed', 409, claimed_by_name=_display(doc.claimed_by))
        if not doc.document:
            return _refuse('no_file', 409)
        if review is None:
            if not wanted:
                return JsonResponse({'success': True, 'removed_pages': [], 'has_original': False})
            review = DocumentReview(document=doc, team_id=doc.team_id)

        current = doc.document.name
        original = review.original_file or current
        earlier = {e.get('page'): e for e in _removed_pages(review) if isinstance(e, dict)}
        now = timezone.now().isoformat()
        entries = [earlier.get(page) or {
            'page': page, 'by': request.user.id, 'by_name': _display(request.user), 'at': now,
            'reason': str(reasons.get(str(page)) or '')[:60],
        } for page in sorted(wanted)]

        if wanted:
            doc.document = upload
            doc.file_size = upload.size
            review.original_file = original
        else:
            doc.document.name = original
            try:
                doc.file_size = default_storage.size(original)
            except Exception:
                doc.file_size = None
            review.original_file = ''
        doc.extracted_text = None
        doc.extracted_text_at = None
        doc.extracted_text_version = None
        doc.save(update_fields=['document', 'file_size', 'extracted_text', 'extracted_text_at',
                                'extracted_text_version'])
        review.removed_pages = json.dumps(entries)
        review.save()
        # An earlier kept-pages file is no longer anyone's; the file as
        # received is never deleted here.
        if current != original and current != doc.document.name:
            try:
                default_storage.delete(current)
            except Exception:
                LOGGER.exception('could not delete a superseded kept-pages file')
        if doc.patient_id:
            # Manual stamp: the chart is not in the URL.
            touch_patient_stamp(doc.patient_id)

    _log('fax_review_pages', request, document_id=doc.id, removed=sorted(wanted))
    return JsonResponse({'success': True, 'removed_pages': entries, 'has_original': bool(review.original_file),
                         'file_size': doc.file_size})


@csrf_exempt
@login_required
def mobile_fax_review_original(request, document_id):
    """GET -> the fax as received, every page. 404 (JSON) when no page was
    ever removed: the document's own file is then the original."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    doc = Document.objects.filter(id=document_id).first()
    if doc is None or not _can_reach(request.user, doc):
        return _not_found()
    review = DocumentReview.objects.filter(document=doc).first()
    if review is None or not review.original_file or not default_storage.exists(review.original_file):
        return _refuse('no_original', 404)
    response = FileResponse(default_storage.open(review.original_file, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="original.pdf"'
    return response
