"""Check-in on an iPad (2026-11-17, SBR1 PLAN_IPAD_CHECK_IN_2026-11.md).

When a patient arrives, a staff member sends a form from the Mac to one of
the clinic's iPads, hands the iPad over, and gets it back with the answers
(and, when asked, a photo for the chart) on the server. Rules, each
load-bearing:

  * **The iPad never holds a staff login.** It is paired once with a short
    code made on a Mac, then signs every request with a random token whose
    SHA-256 is all the server keeps. The token opens the `checkin/kiosk/...`
    routes below and nothing else: every other route authenticates by
    session cookie, which the iPad never has. These routes ignore any
    session cookie too, so a staff login can't act as a device.
  * **The iPad sees one patient at a time, and only after they prove who
    they are.** Until the date of birth matches (or the last name, for a
    chart with no date of birth), the iPad knows only that a form is
    waiting: no name, no form, no prefilled phone. Three wrong tries lock
    the form (`locked`) and the Mac says so.
  * **One form per iPad at a time.** Sending a new one cancels the one that
    was waiting or open on that iPad.
  * **Submitting files the form to the chart at once**, as a PDF document
    written here, with its text stored as the document's text so chart
    search finds it without OCR. The staff member who sent it is the
    document's author. The chart's stamp moves.
  * **The photo and any new phone or email reach the chart only when a staff
    member applies them** (`apply`). A wrong patient's face must never
    become a chart photo by itself. Applying writes the profile and moves
    the chart's stamp; nothing is applied twice.
  * **A retried submit files nothing twice** (`submit_client_uuid`), and a
    retried send creates nothing twice (`client_uuid`).
  * **Staff only, on charts they can open.** Patients and strangers get a
    JSON 404, so the app can tell a refusal from a server without these
    routes (an HTML 404).
  * **The photo is re-encoded as JPEG here** (at most 1200 px, EXIF gone,
    turned upright), so nothing from the iPad's camera metadata is kept.

`CHECK_IN_ENABLED=false` switches it off: the device list answers
`enabled: false`, and every other route answers 503 `check_in_disabled`.
"""
import datetime
import hashlib
import io
import json
import logging
import secrets
import uuid

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.http import FileResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from emr import check_in_forms as forms
from emr import simple_pdf
from emr.models import CheckInDevice, CheckInSession, Document, PortraitHistory, UserProfile
from emr.mutation_stamp import touch_patient_stamp
from emr.portrait_history import set_new_portrait
from problems_app.operations import add_problem_activity

from . import views as api

LOGGER = logging.getLogger('smallbrain.checkin')

PAIRING_MINUTES = 15
WAIT_MINUTES = 30          # sent, nobody has started it
FILL_MINUTES = 60          # started, not yet submitted
VERIFY_ATTEMPTS = 3
PHOTO_MAX_BYTES = 15 * 1024 * 1024
PHOTO_MAX_SIDE = 1200
RECENT_HOURS = 12          # closed sessions still listed, so the Mac can say what happened
_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'  # no 0/O, 1/I/L
OPEN = ('waiting', 'verified')


def enabled():
    return bool(getattr(settings, 'CHECK_IN_ENABLED', True))


def _log(event, **fields):
    LOGGER.info(json.dumps(dict(
        severity='INFO', message=event, event=event,
        serviceContext={'service': 'smallbrain-api'}, **fields), default=str))


def _refuse(error, http_status, **extra):
    return JsonResponse(dict(success=False, error=error, **extra), status=http_status)


def _not_found():
    return _refuse('not_found', 404)


def _disabled():
    return _refuse('check_in_disabled', 503)


def _hash(secret):
    return hashlib.sha256(secret.encode('utf-8')).hexdigest()


def _body(request):
    try:
        value = json.loads(request.body or b'{}')
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _display(user):
    if user is None:
        return ''
    return user.get_full_name() or user.username


def _iso(dt):
    return dt.isoformat() if dt else None


def _is_staff(user):
    return api._fax_caller_is_staff(user)


def _civil_dob(profile):
    """The chart's date of birth as the app reads it: the date part of the
    stored instant in UTC (Detroit-midnight rows and legacy UTC-midnight
    rows both land on the right day; see SyncMappers.parseCivilDate)."""
    if profile is None or profile.date_of_birth is None:
        return None
    return profile.date_of_birth.astimezone(datetime.timezone.utc).date()


def _profile(user):
    try:
        return user.profile
    except UserProfile.DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Expiry, done lazily: nothing on the server runs on a schedule.
# ---------------------------------------------------------------------------

def _deadline(session):
    if session.status == 'waiting':
        return session.created_at + datetime.timedelta(minutes=WAIT_MINUTES)
    if session.status == 'verified':
        return (session.verified_at or session.created_at) + datetime.timedelta(minutes=FILL_MINUTES)
    return None


def _expire_if_due(session, now=None):
    deadline = _deadline(session)
    if deadline is not None and (now or timezone.now()) >= deadline:
        session.status = 'expired'
        session.closed_at = now or timezone.now()
        session.save(update_fields=['status', 'closed_at'])
        _log('checkin_expired', session_id=session.id, device_id=session.device_id)
        return True
    return False


# ---------------------------------------------------------------------------
# JSON shapes
# ---------------------------------------------------------------------------

def device_json(device, now=None):
    now = now or timezone.now()
    if device.revoked_at:
        state = 'removed'
    elif device.token_hash:
        state = 'paired'
    elif device.pairing_expires_at and device.pairing_expires_at > now:
        state = 'pairing'
    else:
        state = 'unpaired'
    return {
        'id': device.id,
        'name': device.name,
        'state': state,
        'paired_at': _iso(device.paired_at),
        'last_seen_at': _iso(device.last_seen_at),
        'pairing_expires_at': _iso(device.pairing_expires_at) if state == 'pairing' else None,
    }


def session_json(session, include_answers=False):
    definition = forms.form(session.form_key)
    data = {
        'id': session.id,
        'patient_id': session.patient_id,
        'patient_name': _display(session.patient),
        'device_id': session.device_id,
        'device_name': session.device.name if session.device_id else '',
        'form_key': session.form_key,
        'form_title': definition['title'] if definition else session.form_key,
        'status': session.status,
        'sent_by_name': _display(session.sent_by),
        'created_at': _iso(session.created_at),
        'verified_at': _iso(session.verified_at),
        'submitted_at': _iso(session.submitted_at),
        'closed_at': _iso(session.closed_at),
        'reviewed_at': _iso(session.reviewed_at),
        'reviewed_by_name': _display(session.reviewed_by),
        'has_photo': bool(session.photo and session.photo.name),
        'document_id': session.document_id,
        'applied': _json_list(session.applied),
    }
    if include_answers:
        answers = _json_dict(session.answers)
        data['answers'] = [
            {'question': q, 'answer': a}
            for q, a in (forms.answered_lines(definition, answers) if definition else [])
        ]
        profile = _profile(session.patient)
        data['proposed'] = _proposed_changes(session.patient, profile, answers)
        data['flags'] = forms.flags(definition, answers) if definition else []
        data['urgent'] = forms.urgent(definition, answers) if definition else []
        data['scores'] = [{'name': x['name'], 'total': x['total'], 'band': x['band']}
                          for x in (forms.scores(definition, answers) if definition else [])]
    return data


def _json_list(text):
    try:
        value = json.loads(text or '[]')
    except ValueError:
        return []
    return value if isinstance(value, list) else []


def _json_dict(text):
    try:
        value = json.loads(text or '{}')
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def _proposed_changes(patient, profile, answers):
    """Phone and email the patient typed that differ from the chart."""
    out = []
    current_phone = forms.normalize_phone(profile.phone_number if profile else '') or (profile.phone_number if profile else '')
    if answers.get('phone') and answers['phone'] != current_phone:
        out.append({'field': 'phone', 'current': (profile.phone_number if profile else '') or '', 'new': answers['phone']})
    if answers.get('email') and answers['email'].lower() != (patient.email or '').lower():
        out.append({'field': 'email', 'current': patient.email or '', 'new': answers['email']})
    return out


# ---------------------------------------------------------------------------
# The device's own routes (token auth, no session)
# ---------------------------------------------------------------------------

def _device_for(request):
    header = request.META.get('HTTP_AUTHORIZATION', '')
    if not header.startswith('Bearer '):
        return None
    token = header[len('Bearer '):].strip()
    if not token:
        return None
    device = CheckInDevice.objects.filter(token_hash=_hash(token), revoked_at__isnull=True).first()
    if device is None:
        return None
    now = timezone.now()
    if device.last_seen_at is None or now - device.last_seen_at > datetime.timedelta(seconds=60):
        CheckInDevice.objects.filter(pk=device.pk).update(last_seen_at=now)
    return device


def _unpaired():
    return _refuse('device_not_paired', 401)


def _device_session(device, session_id, lock=False):
    qs = CheckInSession.objects.filter(pk=session_id, device=device)
    if lock:
        qs = qs.select_for_update()
    return qs.select_related('patient').first()


@csrf_exempt
def kiosk_pair(request):
    """POST {code, name?} -> {token, device_id, device_name}. The code is
    made on a Mac (staff `devices` / `device_pairing_code`), works once, and
    for 15 minutes."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    if not enabled():
        return _disabled()
    code = ''.join(ch for ch in str(_body(request).get('code', '')).upper() if ch.isalnum())
    if len(code) != 8:
        return _refuse('bad_code', 400)
    now = timezone.now()
    with transaction.atomic():
        device = (CheckInDevice.objects.select_for_update()
                  .filter(pairing_code_hash=_hash(code), pairing_expires_at__gt=now).first())
        if device is None:
            _log('checkin_pair_refused')
            return _refuse('bad_code', 400)
        token = secrets.token_urlsafe(32)
        device.token_hash = _hash(token)
        device.pairing_code_hash = ''
        device.pairing_expires_at = None
        device.paired_at = now
        device.last_seen_at = now
        device.revoked_at = None
        device.save()
    _log('checkin_paired', device_id=device.id)
    return JsonResponse({'success': True, 'token': token, 'device_id': device.id, 'device_name': device.name})


@csrf_exempt
def kiosk_current(request):
    """GET -> what this iPad should show: `session` is null, or the form
    waiting for it. Before the patient proves who they are, the session
    carries no name, no form and no prefill."""
    device = _device_for(request)
    if device is None:
        return _unpaired()
    if not enabled():
        return _disabled()
    now = timezone.now()
    session = (CheckInSession.objects.filter(device=device, status__in=OPEN)
               .select_related('patient').order_by('-created_at').first())
    if session is not None and _expire_if_due(session, now):
        session = None
    payload = {'success': True, 'device_name': device.name, 'session': None}
    if session is not None:
        payload['session'] = _kiosk_session_json(session)
    return JsonResponse(payload)


def _kiosk_session_json(session):
    profile = _profile(session.patient)
    data = {
        'id': session.id,
        'status': session.status,
        'verify': 'date_of_birth' if _civil_dob(profile) else 'last_name',
        'attempts_left': max(0, VERIFY_ATTEMPTS - session.verify_attempts),
    }
    if session.status == 'verified':
        data.update(_kiosk_open_form(session, profile))
    return data


def _kiosk_open_form(session, profile):
    definition = forms.form(session.form_key)
    prefill = {}
    for field in forms.fields(definition):
        source = field.get('prefill')
        if source == 'phone' and profile and profile.phone_number:
            prefill[field['key']] = forms.normalize_phone(profile.phone_number) or profile.phone_number
        elif source == 'email' and session.patient.email:
            prefill[field['key']] = session.patient.email
    return {
        'first_name': session.patient.first_name or '',
        'form': definition,
        'prefill': prefill,
        'has_photo': bool(session.photo and session.photo.name),
    }


@csrf_exempt
def kiosk_verify(request, session_id):
    """POST {date_of_birth: "YYYY-MM-DD"} (or {last_name} when the chart has
    no date of birth) -> the open form. Three wrong tries lock it."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    device = _device_for(request)
    if device is None:
        return _unpaired()
    if not enabled():
        return _disabled()
    body = _body(request)
    with transaction.atomic():
        session = _device_session(device, session_id, lock=True)
        if session is None:
            return _not_found()
        if session.status == 'verified':
            return JsonResponse(dict(success=True, session=_kiosk_session_json(session)))
        if session.status != 'waiting' or _expire_if_due(session):
            return _refuse('not_open', 409, status=session.status)
        profile = _profile(session.patient)
        dob = _civil_dob(profile)
        if dob is not None:
            try:
                given = datetime.date.fromisoformat(str(body.get('date_of_birth', '')))
            except ValueError:
                given = None
            matched = given == dob
        else:
            typed = ' '.join(str(body.get('last_name', '')).split()).lower()
            matched = bool(typed) and typed == ' '.join((session.patient.last_name or '').split()).lower()
        if not matched:
            session.verify_attempts += 1
            fields = ['verify_attempts']
            if session.verify_attempts >= VERIFY_ATTEMPTS:
                session.status = 'locked'
                session.closed_at = timezone.now()
                fields += ['status', 'closed_at']
            session.save(update_fields=fields)
            _log('checkin_verify_failed', session_id=session.id, attempts=session.verify_attempts)
            if session.status == 'locked':
                return _refuse('locked', 409, status='locked')
            return _refuse('no_match', 400, attempts_left=VERIFY_ATTEMPTS - session.verify_attempts)
        session.status = 'verified'
        session.verified_at = timezone.now()
        session.save(update_fields=['status', 'verified_at'])
    _log('checkin_verified', session_id=session.id)
    return JsonResponse(dict(success=True, session=_kiosk_session_json(session)))


@csrf_exempt
def kiosk_photo(request, session_id):
    """POST multipart `file` (a JPEG or HEIC from the iPad camera): the
    patient's photo, kept on the session until staff apply it."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    device = _device_for(request)
    if device is None:
        return _unpaired()
    if not enabled():
        return _disabled()
    upload = request.FILES.get('file')
    if upload is None:
        return _refuse('no_file', 400)
    if upload.size > PHOTO_MAX_BYTES:
        return _refuse('too_large', 400)
    jpeg = _clean_photo(upload.read())
    if jpeg is None:
        return _refuse('not_an_image', 400)
    with transaction.atomic():
        session = _device_session(device, session_id, lock=True)
        if session is None:
            return _not_found()
        if session.status != 'verified' or _expire_if_due(session):
            return _refuse('not_open', 409, status=session.status)
        old = session.photo.name if session.photo else ''
        session.photo.save('photo.jpg', ContentFile(jpeg), save=False)
        session.save(update_fields=['photo'])
    if old:
        _delete_quietly(old)
    _log('checkin_photo', session_id=session.id, bytes=len(jpeg))
    return JsonResponse({'success': True})


def _clean_photo(raw):
    """JPEG bytes: upright, at most PHOTO_MAX_SIDE px, RGB, no metadata.
    None when `raw` is not an image Pillow can read."""
    from PIL import Image, ImageOps
    try:
        image = Image.open(io.BytesIO(raw))
        image.load()
    except Exception:
        return None
    image = ImageOps.exif_transpose(image)
    image = image.convert('RGB')
    image.thumbnail((PHOTO_MAX_SIDE, PHOTO_MAX_SIDE))
    out = io.BytesIO()
    image.save(out, format='JPEG', quality=85)
    return out.getvalue()


def _delete_quietly(name):
    from django.core.files.storage import default_storage
    try:
        default_storage.delete(name)
    except Exception:
        LOGGER.exception('check-in photo delete failed (non-fatal)')


@csrf_exempt
def kiosk_submit(request, session_id):
    """POST {client_uuid, answers} -> files the form to the chart. A retry
    with the same client_uuid answers `already: true` and files nothing."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    device = _device_for(request)
    if device is None:
        return _unpaired()
    if not enabled():
        return _disabled()
    body = _body(request)
    client_uuid = str(body.get('client_uuid') or '').strip()
    if not client_uuid or len(client_uuid) > 64:
        return _refuse('client_uuid_required', 400)
    with transaction.atomic():
        session = _device_session(device, session_id, lock=True)
        if session is None:
            return _not_found()
        if session.status in ('submitted', 'reviewed'):
            if session.submit_client_uuid == client_uuid:
                return JsonResponse({'success': True, 'already': True})
            return _refuse('not_open', 409, status=session.status)
        if session.status != 'verified' or _expire_if_due(session):
            return _refuse('not_open', 409, status=session.status)
        definition = forms.form(session.form_key)
        try:
            answers = forms.clean_answers(definition, body.get('answers', {}))
        except forms.AnswerError as error:
            return _refuse(error.code, 400, field=error.field)
        has_photo = bool(session.photo and session.photo.name)
        if definition['photo'] and definition['photo'].get('required') and not has_photo:
            return _refuse('photo_required', 400)
        now = timezone.now()
        session.answers = json.dumps(answers)
        session.status = 'submitted'
        session.submitted_at = now
        session.submit_client_uuid = client_uuid
        # A form with no questions (the photo-only form) files no document:
        # the photo itself is what staff apply.
        if forms.fields(definition):
            session.document = _file_form(session, definition, answers, now)
        session.save(update_fields=['answers', 'status', 'submitted_at', 'submit_client_uuid', 'document'])
        touch_patient_stamp(session.patient_id)
    _log('checkin_submitted', session_id=session.id, form=session.form_key,
         answered=len(answers), photo=has_photo, document_id=session.document_id,
         urgent=bool(forms.urgent(definition, answers)))
    return JsonResponse({'success': True, 'already': False})


def _file_form(session, definition, answers, now):
    """The completed form as a PDF on the chart. Its text is stored as the
    document's text, so chart search finds it without anyone reading it."""
    patient = session.patient
    profile = _profile(patient)
    local = timezone.localtime(now)
    title = '%s form' % definition['title']
    name = '%s %s' % (title, local.strftime('%-m/%-d/%Y'))

    header = [
        'Patient: %s' % _display(patient),
    ]
    dob = _civil_dob(profile)
    if dob:
        header.append('Date of birth: %s' % dob.strftime('%-m/%-d/%Y'))
    header.append('Filled in by the patient on the check-in iPad "%s"' % (session.device.name if session.device_id else ''))
    header.append('Submitted %s' % local.strftime('%-m/%-d/%Y %-I:%M %p'))
    header.append('Sent by %s' % _display(session.sent_by))
    if session.photo and session.photo.name:
        header.append('A photo was taken (it reaches the chart only when staff apply it).')
    lines = forms.answered_lines(definition, answers)
    flagged = forms.flags(definition, answers)
    urgent = forms.urgent(definition, answers)
    scored = forms.scores(definition, answers)

    doc = simple_pdf.Document()
    free = 0
    if session.photo and session.photo.name:
        free = _place_photo(doc, session)
    width = simple_pdf.PAGE_W - 2 * simple_pdf.MARGIN - free
    doc.text(title, size=18, bold=True, gap_after=10, width=width)
    for line in header:
        doc.text(line, size=10, gap_after=2, width=width)
    doc.below_image()
    doc.space(10)
    if urgent:
        doc.text('URGENT — act before the patient leaves', size=12, bold=True, gap_after=2)
        for item in urgent:
            doc.text('- %s' % item, size=11, gap_after=2, indent=12)
        doc.space(10)
    if scored:
        doc.text('Scores', size=12, bold=True, gap_after=2)
        for score in scored:
            doc.text('- %s: %d (%s)' % (score['name'], score['total'], score['band']), size=11,
                     gap_after=2, indent=12)
        doc.space(10)
    if flagged:
        doc.text('For the care team to follow up', size=12, bold=True, gap_after=2)
        for item in flagged:
            doc.text('- %s' % item, size=11, gap_after=2, indent=12)
        doc.space(10)
    for question, answer in lines:
        doc.text(question, size=11, bold=True, gap_after=2)
        doc.text(answer, size=11, gap_after=10, indent=12)
    if not lines:
        doc.text('(This form has no questions.)', size=11)

    text = '\n'.join([title] + header
                      + (['URGENT — act before the patient leaves'] + urgent if urgent else [])
                      + (['Scores'] + ['%s: %d (%s)' % (x['name'], x['total'], x['band']) for x in scored]
                         if scored else [])
                      + (['For the care team to follow up'] + flagged if flagged else [])
                      + ['%s\n%s' % (q, a) for q, a in lines])
    document = Document(
        document_name=name,
        author=session.sent_by or patient,
        patient=patient,
        client_uuid=uuid.uuid5(uuid.NAMESPACE_URL, 'smallbrain-check-in/%d' % session.id),
        original_file_name='%s.pdf' % name.replace('/', '-'),
        extracted_text=text,
        extracted_text_at=now,
    )
    pdf = doc.render()
    document.file_size = len(pdf)
    document.document.save('check-in.pdf', ContentFile(pdf), save=False)
    document.save()
    add_problem_activity(None, session.sent_by or patient,
                         'Added document: %s (filled in by the patient on the check-in iPad)' % name)
    return document


def _place_photo(doc, session):
    from PIL import Image
    try:
        with session.photo.open('rb') as handle:
            jpeg = handle.read()
        width, height = Image.open(io.BytesIO(jpeg)).size
    except Exception:
        LOGGER.exception('check-in photo unreadable while filing (non-fatal)')
        return 0
    return doc.image_top_right(jpeg, width, height)


@csrf_exempt
def kiosk_abandon(request, session_id):
    """POST -> the patient walked away mid-form (the iPad's idle timer).
    Nothing was filed; the Mac can send the form again."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    device = _device_for(request)
    if device is None:
        return _unpaired()
    with transaction.atomic():
        session = _device_session(device, session_id, lock=True)
        if session is None:
            return _not_found()
        if session.status in OPEN:
            session.status = 'abandoned'
            session.closed_at = timezone.now()
            session.save(update_fields=['status', 'closed_at'])
            _log('checkin_abandoned', session_id=session.id)
    return JsonResponse({'success': True, 'status': session.status})


# ---------------------------------------------------------------------------
# Staff routes (session auth)
# ---------------------------------------------------------------------------

def _new_pairing_code(device):
    code = ''.join(secrets.choice(_CODE_ALPHABET) for _ in range(8))
    device.pairing_code_hash = _hash(code)
    device.pairing_expires_at = timezone.now() + datetime.timedelta(minutes=PAIRING_MINUTES)
    return code


@csrf_exempt
@login_required
def mobile_check_in_devices(request):
    """GET -> {enabled, devices, forms}. POST {name} -> a new device and its
    pairing code (shown once; type it on the iPad within 15 minutes)."""
    if not _is_staff(request.user):
        return _not_found()
    if request.method == 'GET':
        if not enabled():
            return JsonResponse({'success': True, 'enabled': False, 'devices': [], 'forms': []})
        now = timezone.now()
        devices = CheckInDevice.objects.filter(revoked_at__isnull=True).order_by('name', 'id')
        return JsonResponse({'success': True, 'enabled': True,
                             'devices': [device_json(d, now) for d in devices],
                             'forms': forms.summaries()})
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    if not enabled():
        return _disabled()
    name = ' '.join(str(_body(request).get('name', '')).split())[:80]
    if not name:
        return _refuse('name_required', 400)
    device = CheckInDevice(name=name, created_by=request.user)
    code = _new_pairing_code(device)
    device.save()
    _log('checkin_device_added', device_id=device.id, actor_id=request.user.id)
    return JsonResponse({'success': True, 'device': device_json(device), 'pairing_code': code})


@csrf_exempt
@login_required
def mobile_check_in_device_pairing_code(request, device_id):
    """POST -> a new pairing code for an iPad (a replaced iPad, or one whose
    app was deleted). The old token stops working at once."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    if not _is_staff(request.user):
        return _not_found()
    if not enabled():
        return _disabled()
    device = CheckInDevice.objects.filter(pk=device_id, revoked_at__isnull=True).first()
    if device is None:
        return _not_found()
    code = _new_pairing_code(device)
    device.token_hash = ''
    device.paired_at = None
    device.save()
    _log('checkin_device_repair', device_id=device.id, actor_id=request.user.id)
    return JsonResponse({'success': True, 'device': device_json(device), 'pairing_code': code})


@csrf_exempt
@login_required
def mobile_check_in_device_remove(request, device_id):
    """POST -> the iPad can do nothing more (lost, retired). Its open form
    is cancelled."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    if not _is_staff(request.user):
        return _not_found()
    device = CheckInDevice.objects.filter(pk=device_id, revoked_at__isnull=True).first()
    if device is None:
        return _not_found()
    now = timezone.now()
    with transaction.atomic():
        device.revoked_at = now
        device.token_hash = ''
        device.pairing_code_hash = ''
        device.pairing_expires_at = None
        device.save()
        CheckInSession.objects.filter(device=device, status__in=OPEN).update(status='cancelled', closed_at=now)
    _log('checkin_device_removed', device_id=device.id, actor_id=request.user.id)
    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_check_in_send(request, patient_id):
    """POST {device_id, form_key, client_uuid} -> the session. Cancels
    whatever was waiting or open on that iPad."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    if not (_is_staff(request.user) and api._assert_patient_access(request.user, patient_id)):
        return _not_found()
    if not enabled():
        return _disabled()
    body = _body(request)
    client_uuid = str(body.get('client_uuid') or '').strip()
    if not client_uuid or len(client_uuid) > 64:
        return _refuse('client_uuid_required', 400)
    existing = CheckInSession.objects.filter(client_uuid=client_uuid).select_related('patient', 'device', 'sent_by').first()
    if existing is not None:
        if existing.patient_id != int(patient_id):
            return _refuse('client_uuid_reused', 409)
        return JsonResponse({'success': True, 'already': True, 'session': session_json(existing)})
    form_key = str(body.get('form_key') or '')
    definition = forms.form(form_key)
    if definition is None:
        return _refuse('unknown_form', 400)
    try:
        device_id = int(body.get('device_id'))
    except (TypeError, ValueError):
        return _refuse('device_required', 400)
    patient = User.objects.filter(pk=patient_id).first()
    if patient is None:
        return _not_found()
    now = timezone.now()
    try:
        with transaction.atomic():
            device = CheckInDevice.objects.select_for_update().filter(pk=device_id, revoked_at__isnull=True).first()
            if device is None:
                return _refuse('unknown_device', 400)
            if not device.token_hash:
                return _refuse('device_not_paired', 409)
            replaced = list(CheckInSession.objects.filter(device=device, status__in=OPEN).values_list('id', flat=True))
            CheckInSession.objects.filter(id__in=replaced).update(status='cancelled', closed_at=now)
            session = CheckInSession.objects.create(
                device=device, patient=patient, sent_by=request.user,
                form_key=definition['key'], form_version=definition['version'],
                client_uuid=client_uuid)
    except IntegrityError:
        existing = CheckInSession.objects.filter(client_uuid=client_uuid).first()
        if existing is None:
            raise
        return JsonResponse({'success': True, 'already': True, 'session': session_json(existing)})
    _log('checkin_sent', session_id=session.id, device_id=device.id, form=session.form_key,
         actor_id=request.user.id, replaced=replaced)
    return JsonResponse({'success': True, 'already': False, 'session': session_json(session)})


@csrf_exempt
@login_required
def mobile_check_in_sessions(request):
    """GET [?patient_id=] -> {open, to_review, recent} for charts the caller
    can open. `to_review` carries the answers and the proposed changes."""
    if not _is_staff(request.user):
        return _not_found()
    if not enabled():
        return JsonResponse({'success': True, 'enabled': False, 'open': [], 'to_review': [], 'recent': []})
    now = timezone.now()
    qs = CheckInSession.objects.select_related('patient', 'device', 'sent_by', 'reviewed_by')
    accessible = api._accessible_patient_ids(request.user)
    if accessible is not None:
        qs = qs.filter(patient_id__in=accessible)
    patient_id = request.GET.get('patient_id')
    if patient_id:
        try:
            qs = qs.filter(patient_id=int(patient_id))
        except ValueError:
            return _refuse('bad_patient_id', 400)
    open_rows, review_rows, recent_rows = [], [], []
    for session in qs.filter(status__in=OPEN).order_by('-created_at')[:50]:
        if _expire_if_due(session, now):
            recent_rows.append(session_json(session))
        else:
            open_rows.append(session_json(session))
    for session in qs.filter(status='submitted').order_by('-submitted_at')[:50]:
        review_rows.append(session_json(session, include_answers=True))
    since = now - datetime.timedelta(hours=RECENT_HOURS)
    for session in (qs.filter(status__in=('reviewed', 'cancelled', 'locked', 'abandoned', 'expired'),
                              closed_at__gte=since).order_by('-closed_at')[:50]):
        recent_rows.append(session_json(session))
    payload = {'success': True, 'enabled': True, 'server_time': _iso(now),
               'open': open_rows, 'to_review': review_rows, 'recent': recent_rows}
    if patient_id:
        # When each form was last finished for this patient: the PCMH
        # partnership discussion is repeated at least every 2-3 years, and
        # the Mac shows the date beside the form.
        last = {}
        for form_key, submitted in (qs.filter(status__in=('submitted', 'reviewed'))
                                    .order_by('form_key', '-submitted_at')
                                    .values_list('form_key', 'submitted_at')):
            last.setdefault(form_key, _iso(submitted))
        payload['last_completed'] = last
    return JsonResponse(payload)


def _staff_session(request, session_id, lock=False):
    if not _is_staff(request.user):
        return None
    qs = CheckInSession.objects.filter(pk=session_id)
    if lock:
        qs = qs.select_for_update()
    session = qs.select_related('patient', 'device', 'sent_by', 'reviewed_by').first()
    if session is None or not api._assert_patient_access(request.user, session.patient_id):
        return None
    return session


@csrf_exempt
@login_required
def mobile_check_in_cancel(request, session_id):
    """POST -> take a waiting or open form back (the iPad goes back to its
    welcome screen within a few seconds)."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    with transaction.atomic():
        session = _staff_session(request, session_id, lock=True)
        if session is None:
            return _not_found()
        if session.status in OPEN:
            session.status = 'cancelled'
            session.closed_at = timezone.now()
            session.save(update_fields=['status', 'closed_at'])
            _log('checkin_cancelled', session_id=session.id, actor_id=request.user.id)
    return JsonResponse({'success': True, 'session': session_json(session)})


@csrf_exempt
@login_required
def mobile_check_in_photo(request, session_id):
    """GET -> the photo the patient took, for staff to look at before
    applying it."""
    session = _staff_session(request, session_id)
    if session is None or not (session.photo and session.photo.name):
        return _not_found()
    try:
        return FileResponse(session.photo.open('rb'), content_type='image/jpeg')
    except Exception:
        return _not_found()


@csrf_exempt
@login_required
def mobile_check_in_apply(request, session_id):
    """POST {photo: bool, phone: bool, email: bool} -> applies what the
    staff member ticked to the chart and marks the check-in reviewed.
    All false = reviewed, nothing applied. A reviewed check-in answers
    409 `already_reviewed` and applies nothing."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    if not enabled():
        return _disabled()
    body = _body(request)
    with transaction.atomic():
        session = _staff_session(request, session_id, lock=True)
        if session is None:
            return _not_found()
        if session.status == 'reviewed':
            return _refuse('already_reviewed', 409, session=session_json(session))
        if session.status != 'submitted':
            return _refuse('not_submitted', 409, status=session.status)
        patient = session.patient
        profile, _ = UserProfile.objects.get_or_create(user=patient)
        answers = _json_dict(session.answers)
        applied = []
        old = {'phone': profile.phone_number, 'email': patient.email}
        if body.get('photo') is True:
            if not (session.photo and session.photo.name):
                return _refuse('no_photo', 400)
            with session.photo.open('rb') as handle:
                jpeg = handle.read()
            # A unique name every time (GCS overwrites by default); the
            # save below keeps the photo this one replaces (PortraitHistory).
            set_new_portrait(profile, jpeg, actor=request.user, source=PortraitHistory.SOURCE_CHECK_IN)
            applied.append('photo')
        if body.get('phone') is True and answers.get('phone'):
            profile.phone_number = answers['phone']
            applied.append('phone')
        if body.get('email') is True and answers.get('email'):
            patient.email = answers['email']
            patient.save(update_fields=['email'])
            applied.append('email')
        if applied:
            profile.save()
        session.status = 'reviewed'
        session.reviewed_at = session.closed_at = timezone.now()
        session.reviewed_by = request.user
        session.applied = json.dumps(applied)
        session.save(update_fields=['status', 'reviewed_at', 'closed_at', 'reviewed_by', 'applied'])
        if applied:
            touch_patient_stamp(patient.id)
            add_problem_activity(None, request.user, 'Updated from check-in: %s' % ', '.join(
                {'photo': 'chart photo', 'phone': 'phone number', 'email': 'email address'}[a] for a in applied))
    if applied:
        logging.getLogger('smallbrain.profile_edits').info(json.dumps({
            'event': 'profile_edited', 'source': 'check_in', 'session_id': session.id,
            'fields': ['portrait_image' if a == 'photo' else a for a in applied],
            'editor_id': request.user.id, 'target_user_id': patient.id,
            'old_phone_set': bool(old['phone']), 'old_email_set': bool(old['email']),
        }))
    _log('checkin_reviewed', session_id=session.id, applied=applied, actor_id=request.user.id)
    return JsonResponse({'success': True, 'session': session_json(session),
                         'portrait_version': portrait_version(profile)})


# ---------------------------------------------------------------------------
# The chart photo
# ---------------------------------------------------------------------------

portrait_version = api.portrait_version


@csrf_exempt
@login_required
def mobile_portrait_file(request, user_id):
    """GET -> the patient's chart photo, for staff who can open the chart
    and the patient themselves (`_assert_patient_access`)."""
    if not api._assert_patient_access(request.user, user_id):
        return _not_found()
    user = User.objects.filter(pk=user_id).select_related('profile').first()
    profile = _profile(user) if user else None
    if portrait_version(profile) is None:
        return _not_found()
    try:
        return FileResponse(profile.portrait_image.open('rb'), content_type='image/jpeg')
    except Exception:
        return _not_found()


@csrf_exempt
@login_required
def mobile_user_portrait_upload(request, user_id):
    """POST multipart `file` -> a new profile photo from the app's Settings →
    Edit Profile (2026-11-21). Answers {success, portrait_version}.

    Who may: the person themself; an admin for anyone; and staff (physician,
    mid-level, nurse, secretary) for a PATIENT whose chart they can open
    (`_assert_patient_access`; owner decision 2026-11-21 — check-in already
    let any staff member with chart access apply a patient's photo).
    Everyone else, and a user that does not exist, gets JSON 404
    `not_found` — never 403, which the app reads as "signed out".

    The photo is re-encoded like a check-in photo (upright, at most
    PHOTO_MAX_SIDE px, no metadata), saved under a fresh random name, and the
    save keeps the photo it replaces (`PortraitHistory`, source `app`). A
    patient's chart stamp moves, so an open chart on another Mac pulls the new
    `portrait_version` and downloads the photo."""
    if request.method != 'POST':
        return _refuse('method_not_allowed', 405)
    try:
        target_id = int(user_id)
    except (TypeError, ValueError):
        return _not_found()
    caller_role = getattr(_profile(request.user), 'role', None)
    is_self = request.user.id == target_id
    staff_for_patient = (
        caller_role in ('physician', 'mid-level', 'nurse', 'secretary')
        and UserProfile.objects.filter(user_id=target_id, role='patient').exists()
        and api._assert_patient_access(request.user, target_id))
    if not (is_self or caller_role == 'admin' or staff_for_patient):
        return _not_found()
    target = User.objects.filter(pk=target_id).first()
    if target is None:
        return _not_found()
    upload = request.FILES.get('file')
    if upload is None:
        return _refuse('no_file', 400)
    if upload.size > PHOTO_MAX_BYTES:
        return _refuse('too_large', 400)
    jpeg = _clean_photo(upload.read())
    if jpeg is None:
        return _refuse('not_an_image', 400)
    with transaction.atomic():
        profile, _ = UserProfile.objects.select_for_update().get_or_create(user=target)
        set_new_portrait(profile, jpeg, actor=request.user, source=PortraitHistory.SOURCE_APP)
        profile.save(update_fields=['portrait_image'])
        if profile.role == 'patient':
            touch_patient_stamp(target.id)
    if not is_self:
        logging.getLogger('smallbrain.profile_edits').info(json.dumps({
            'event': 'profile_edited', 'source': 'app', 'fields': ['portrait_image'],
            'editor_id': request.user.id, 'editor_role': caller_role, 'target_user_id': target.id,
        }))
    _log('portrait_changed', user_id=target.id, actor_id=request.user.id, bytes=len(jpeg))
    return JsonResponse({'success': True, 'portrait_version': portrait_version(profile)})
