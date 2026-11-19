"""Waiting faxes on the chart (2026-11-18; SBR1 PLAN_INBOUND_FAX_2026-11.md,
phase 4).

A chart shows the documents still in an unassigned pool that are probably
for that patient: a "2 faxes waiting" chip in the header and a section in
Docs, each with why it matched.

The server cannot read pages (OCR runs on the Macs), so staff Macs read pool
documents in the background (owner decision, same day): a Mac asks
`read-next` for the oldest unread pool document its teams can see and holds
a ten-minute lease on it, so two Macs never read the same one; it reads the
pages, matches them against its roster and reports `read` with the matches
and the text. A chart asks `waiting-faxes` for its patient's matches.

Rules, each load-bearing:

  * **Only documents still in a pool count**: no patient, a team, not in
    Office, not in the retired `set_aside` state. Filing, assigning, moving
    to Office or deleting a document takes it off every chart at once; no
    match row needs cleaning up for that.
  * **A match is a name match found on a Mac.** The server adds one signal
    only it knows, "we faxed this number for this patient in the past 30
    days", and only as a reason on a row that already matched: a lab's
    number is faxed for dozens of patients, so on its own it would put the
    same result on every one of their charts.
  * **"Not this patient" hides a document on one chart only**, and a later
    read keeps it hidden.
  * **A patient the reporting login cannot open is dropped**, and only
    patients are kept (never a staff member whose name is on a page).
  * Staff only; refusals are JSON (never 403: the app reads 403 as signed
    out); `WAITING_FAXES_ENABLED=false` quiets every Mac with no app update.
"""
import json
import logging
import os
import re
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from emr.models import Document, FaxPatientMatch, FaxScan, FaxTransmission
from emr.storable import storable_text

from . import views as api
from .views import touches_patient_stamp

LOGGER = logging.getLogger('smallbrain.waiting_faxes')

LEASE = timedelta(minutes=10)
MAX_READ_ATTEMPTS = 3
MAX_MATCHES = 5
MAX_TEXT_SENT = 20000
FAXED_NUMBER_DAYS = 30
REASONS = ('name', 'full_name', 'last_name', 'dob')


def enabled():
    return getattr(settings, 'WAITING_FAXES_ENABLED', True)


def _log(event, request, **fields):
    LOGGER.info(json.dumps(dict(
        severity='INFO', message=event, event=event, user_id=request.user.id,
        serviceContext={'service': 'smallbrain-api'}, **fields)))


def _refuse(error, status, **extra):
    return JsonResponse(dict({'error': error}, **extra), status=status)


def _not_found():
    return _refuse('not_found', 404)


def _gate(request, method):
    if not api._fax_caller_is_staff(request.user):
        return _not_found()
    if request.method != method:
        return _refuse('%s required' % method, 405)
    if not enabled():
        return _refuse('waiting_faxes_disabled', 503)
    return None


def _body(request):
    try:
        body = json.loads(request.body or b'{}')
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def _pool_documents(user):
    """The pool documents `user` may see: still in a pool, never in Office.
    None when the user sees no pool."""
    allowed = api._user_team_ids(user)
    qs = Document.objects.filter(patient__isnull=True, team__isnull=False).exclude(
        office__isnull=False).exclude(review__state='set_aside')
    if allowed is None:
        return qs  # admin: every pool
    if not allowed:
        return None
    return qs.filter(team_id__in=allowed)


def _last_ten(number):
    digits = re.sub(r'\D', '', number or '')
    return digits[-10:] if len(digits) >= 10 else ''


# ---------------------------------------------------------------------------
# Reading, by a staff Mac in the background
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
def mobile_inbox_read_next(request):
    """POST -> {document_id, file_ext, document_name, lease_seconds} for the
    oldest unread pool document the caller's teams can see, leased to the
    caller for ten minutes; or {none: true}."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    pool = _pool_documents(request.user)
    if pool is None:
        return JsonResponse({'success': True, 'none': True})
    now = timezone.now()
    unread = Q(fax_scan__isnull=True) | (
        Q(fax_scan__scanned_at__isnull=True) & Q(fax_scan__attempts__lt=MAX_READ_ATTEMPTS)
        & (Q(fax_scan__leased_until__isnull=True) | Q(fax_scan__leased_until__lt=now)))
    candidates = list(pool.filter(unread).exclude(document='').order_by('created_on', 'id')
                      .values_list('id', flat=True)[:10])
    for document_id in candidates:
        try:
            FaxScan.objects.get_or_create(document_id=document_id)
        except IntegrityError:
            pass  # another Mac created it a moment ago; the update decides
        # One conditional update is the lease: only one caller can move a
        # row that is unread and unleased.
        leased = FaxScan.objects.filter(
            document_id=document_id, scanned_at__isnull=True, attempts__lt=MAX_READ_ATTEMPTS,
        ).filter(Q(leased_until__isnull=True) | Q(leased_until__lt=now)).update(
            leased_by=request.user, leased_until=now + LEASE)
        if not leased:
            continue
        doc = Document.objects.get(id=document_id)
        ext = os.path.splitext(doc.document.name or '')[1].lower() or '.pdf'
        return JsonResponse({'success': True, 'document_id': doc.id, 'file_ext': ext,
                             'document_name': doc.document_name or '',
                             'lease_seconds': int(LEASE.total_seconds())})
    return JsonResponse({'success': True, 'none': True})


@csrf_exempt
@login_required
def mobile_inbox_read(request, document_id):
    """POST {matches: [{patient_id, strength, reasons}], text, text_version?}
    -> the document is read: its text is stored (characters MySQL cannot
    take become U+FFFD), its matches replace the last read's (dismissals are
    kept). POST {failed: true, error} counts a failed read instead."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    body = _body(request)
    if body is None:
        return _refuse('invalid_json', 400)
    pool = _pool_documents(request.user)
    doc = pool.filter(id=document_id).first() if pool is not None else None
    if doc is None:
        return _not_found()
    now = timezone.now()

    with transaction.atomic():
        try:
            scan, _ = FaxScan.objects.select_for_update().get_or_create(document=doc)
        except IntegrityError:
            scan = FaxScan.objects.select_for_update().get(document=doc)
        if body.get('failed'):
            scan.attempts += 1
            scan.last_error = str(body.get('error') or '')[:255]
            scan.leased_until = None
            scan.save(update_fields=['attempts', 'last_error', 'leased_until'])
            _log('inbox_fax_read_failed', request, document_id=doc.id, attempts=scan.attempts)
            return JsonResponse({'success': True, 'attempts': scan.attempts})

        text = storable_text(body.get('text'))
        if isinstance(text, str) and (text or not doc.extracted_text):
            doc.extracted_text = text
            doc.extracted_text_at = now
            try:
                version = body.get('text_version')
                doc.extracted_text_version = int(version) if version not in (None, '') else None
            except (TypeError, ValueError):
                doc.extracted_text_version = None
            doc.save(update_fields=['extracted_text', 'extracted_text_at', 'extracted_text_version'])

        wanted = {}
        for item in body.get('matches') or []:
            if not isinstance(item, dict) or len(wanted) >= MAX_MATCHES:
                continue
            try:
                patient_id = int(item.get('patient_id'))
            except (TypeError, ValueError):
                continue
            strength = item.get('strength')
            if strength not in (FaxPatientMatch.STRONG, FaxPatientMatch.POSSIBLE) or patient_id in wanted:
                continue
            reasons = [r for r in (item.get('reasons') or []) if r in REASONS]
            wanted[patient_id] = (strength, reasons)
        patients = set(User.objects.filter(id__in=wanted, profile__role='patient').values_list('id', flat=True))
        kept = [pid for pid in wanted if pid in patients and api._assert_patient_access(request.user, pid)]
        for patient_id in kept:
            strength, reasons = wanted[patient_id]
            row, created = FaxPatientMatch.objects.get_or_create(
                document=doc, patient_id=patient_id,
                defaults={'strength': strength, 'reasons': json.dumps(reasons),
                          'found_by': request.user, 'found_at': now})
            if not created:
                row.strength = strength
                row.reasons = json.dumps(reasons)
                row.found_by = request.user
                row.found_at = now
                row.save(update_fields=['strength', 'reasons', 'found_by', 'found_at'])
        # What this read no longer finds goes, unless someone said "not this
        # patient": that answer outlives the read.
        FaxPatientMatch.objects.filter(document=doc, dismissed_at__isnull=True).exclude(
            patient_id__in=kept).delete()
        scan.scanned_by = request.user
        scan.scanned_at = now
        scan.leased_until = None
        scan.last_error = ''
        scan.save(update_fields=['scanned_by', 'scanned_at', 'leased_until', 'last_error'])
    _log('inbox_fax_read', request, document_id=doc.id, matches=len(kept), dropped=len(wanted) - len(kept))
    return JsonResponse({'success': True, 'matches': len(kept)})


# ---------------------------------------------------------------------------
# The chart
# ---------------------------------------------------------------------------

def _row_json(match, faxed_numbers, now):
    doc = match.document
    inbound = getattr(doc, 'inbound_fax', None)
    try:
        reasons = json.loads(match.reasons or '[]')
    except ValueError:
        reasons = []
    claim_live = bool(doc.claimed_by_id and doc.claimed_at
                      and doc.claimed_at >= now - timedelta(seconds=api._UNASSIGNED_CLAIM_TTL_SECONDS))
    from_number = inbound.from_number if inbound is not None else ''
    return {
        'document_id': doc.id,
        'document_name': doc.document_name or '',
        'team_id': doc.team_id,
        'received_at': api._iso_z(inbound.received_at if inbound is not None else doc.created_on),
        'page_count': inbound.page_count if inbound is not None else None,
        'from_number': api._display_fax_number(re.sub(r'\D', '', from_number)) if from_number else '',
        'strength': match.strength,
        'reasons': reasons,
        'faxed_this_number': bool(from_number) and _last_ten(from_number) in faxed_numbers,
        'claimed_by_id': doc.claimed_by_id if claim_live else None,
        'claimed_by_name': (doc.claimed_by.get_full_name() or doc.claimed_by.username) if claim_live else '',
        'found_at': api._iso_z(match.found_at),
        'text': (doc.extracted_text or '')[:MAX_TEXT_SENT],
    }


@csrf_exempt
@login_required
def mobile_patient_waiting_faxes(request, patient_id):
    """GET -> {faxes: the pool documents probably for this patient}, strong
    matches first, newest first. Read-only."""
    if request.method != 'GET':
        return _refuse('GET required', 405)
    if not api._fax_caller_is_staff(request.user) or not api._assert_patient_access(request.user, patient_id):
        return _not_found()
    if not enabled():
        return JsonResponse({'success': True, 'enabled': False, 'faxes': []})
    pool = _pool_documents(request.user)
    if pool is None:
        return JsonResponse({'success': True, 'enabled': True, 'faxes': []})
    now = timezone.now()
    matches = list(FaxPatientMatch.objects.filter(
        patient_id=patient_id, dismissed_at__isnull=True, document__in=pool,
    ).select_related('document', 'document__claimed_by', 'document__inbound_fax'))
    faxed_numbers = {
        _last_ten(number) for number in FaxTransmission.objects.filter(
            patient_id=patient_id, created_on__gte=now - timedelta(days=FAXED_NUMBER_DAYS),
        ).values_list('fax_number', flat=True)} - {''}
    rows = [_row_json(match, faxed_numbers, now) for match in matches]
    rows.sort(key=lambda r: r['received_at'] or '', reverse=True)
    rows.sort(key=lambda r: 0 if r['strength'] == FaxPatientMatch.STRONG else 1)
    return JsonResponse({'success': True, 'enabled': True, 'faxes': rows})


@csrf_exempt
@login_required
@touches_patient_stamp
def mobile_patient_waiting_fax_dismiss(request, patient_id, document_id):
    """POST -> "not this patient": the document stops showing on this chart
    (for everyone); it stays in the pool and on any other chart it matched."""
    refusal = _gate(request, 'POST')
    if refusal:
        return refusal
    if not api._assert_patient_access(request.user, patient_id):
        return _not_found()
    match = FaxPatientMatch.objects.filter(patient_id=patient_id, document_id=document_id).first()
    if match is None:
        return _not_found()
    if match.dismissed_at is None:
        match.dismissed_by = request.user
        match.dismissed_at = timezone.now()
        match.save(update_fields=['dismissed_by', 'dismissed_at'])
        _log('waiting_fax_dismissed', request, document_id=document_id, patient_id=patient_id)
    return JsonResponse({'success': True})
