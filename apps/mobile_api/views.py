"""
Mobile API endpoints for the SBR1 iOS app.
All views are CSRF-exempt and return JSON.
"""
import hashlib
import json
import logging
import mimetypes
import os
import re

from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from emr.models import (
    UserProfile, PatientController, PhysicianTeam,
    Problem, ProblemNote, ProblemLabel, ProblemRelationship, ProblemActivity,
    ToDo, Label, ToDoComment, TodoActivity,
    Observation, ObservationComponent, ObservationValue, ObservationPinToProblem,
    PatientImage,
    Encounter, EncounterEvent, EncounterProblemRecord, EncounterTodoRecord,
    EncounterObservationValue,
    Document, DocumentProblem, DocumentTodo,
    MyStoryTextComponent, MyStoryTextComponentEntry,
    TaggedToDoOrder,
)
from problems_app.operations import add_problem_activity
from todo_app.operations import add_todo_activity


def _strip_html(text):
    """Remove HTML tags from text."""
    return re.sub(r'<[^>]+>', '', text)


def _user_dict(user, profile=None):
    """Serialize a Django User + UserProfile to a flat dict."""
    if profile is None:
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            profile = None
    portrait_url = None
    cover_url = None
    signature_url = None
    if profile:
        try:
            if profile.portrait_image and profile.portrait_image.name and not profile.portrait_image.name.startswith('/static/'):
                portrait_url = profile.portrait_image.url
        except Exception:
            pass
        try:
            if profile.cover_image and profile.cover_image.name and not profile.cover_image.name.startswith('/static/'):
                cover_url = profile.cover_image.url
        except Exception:
            pass
        try:
            if profile.signature_image and profile.signature_image.name:
                # Route through the RBAC-gated proxy rather than handing out
                # the raw GCS URL. Append updated_at as a cache-bust version
                # param so iOS image caches invalidate when the physician
                # redraws their signature.
                version = ''
                if profile.updated_at:
                    version = '?v=%d' % int(profile.updated_at.timestamp())
                signature_url = '/api/media/signature/%d%s' % (user.id, version)
        except Exception:
            pass

    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'role': profile.role if profile else 'patient',
        'is_active': user.is_active,
        'sex': profile.sex if profile else '',
        'date_of_birth': profile.date_of_birth.isoformat() if profile and profile.date_of_birth else None,
        'phone_number': profile.phone_number if profile else '',
        'summary': profile.summary if profile else '',
        'portrait_image_url': portrait_url,
        'cover_image_url': cover_url,
        # Provider identity — populated only for physicians; empty strings
        # for everyone else. iOS reads these off the resolved physician in
        # OrderRequisitionView.
        'credentials': profile.credentials if profile else '',
        'npi_number': profile.npi_number if profile else '',
        'signature_url': signature_url,
        # Practice block — physician's office info; flat denormalized fields.
        'practice_name': profile.practice_name if profile else '',
        'practice_street_address': profile.practice_street_address if profile else '',
        'practice_city': profile.practice_city if profile else '',
        'practice_state': profile.practice_state if profile else '',
        'practice_zip': profile.practice_zip if profile else '',
        'practice_phone': profile.practice_phone if profile else '',
        'practice_fax': profile.practice_fax if profile else '',
    }


@csrf_exempt
def mobile_healthz(request):
    """GET -> 200 with a stable JSON shape. Liveness probe only — no auth,
    no DB check.

    Purpose: lets ops + uptime monitors (UptimeRobot, Better Stack, etc.)
    confirm "Cloud Run is alive and Django is routing" without holding a
    session cookie. A 5xx here = real outage (container crashed, Django
    not booted, networking dropped). A 200 here does NOT guarantee the
    DB is reachable — it confirms the API process is alive.

    Intentionally does NOT touch Cloud SQL: a brief DB hiccup shouldn't
    flap uptime monitoring (cause false-positive pager). Database health
    is monitored separately at the Cloud SQL layer.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)
    return JsonResponse({
        'status': 'ok',
        'service': 'smallbrain-api',
    })


@csrf_exempt
def mobile_login(request):
    """POST {username, password} -> user info + session cookie."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        body = request.POST

    username = body.get('username', '')
    password = body.get('password', '')
    user = authenticate(username=username, password=password)
    if not user or not user.is_active:
        return JsonResponse({'error': 'Invalid credentials'}, status=401)

    login(request, user)

    try:
        request.session.save()
    except Exception:
        import traceback
        return JsonResponse({
            'success': False,
            'error': 'Session save failed: ' + traceback.format_exc(),
        }, status=500)

    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'No profile found'}, status=403)

    try:
        return JsonResponse({
            'success': True,
            'user': _user_dict(user, profile),
            'session_key': request.session.session_key,
        })
    except Exception:
        import traceback
        return JsonResponse({
            'success': False,
            'error': traceback.format_exc(),
        }, status=500)


@csrf_exempt
@login_required
def mobile_change_password(request):
    """POST {current_password, new_password} -> change the logged-in user's password."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    body = _parse_body(request)
    current_password = body.get('current_password', '')
    new_password = body.get('new_password', '')

    if not current_password or not new_password:
        return JsonResponse({'error': 'current_password and new_password are required'}, status=400)

    if len(new_password) < 8:
        return JsonResponse({'error': 'New password must be at least 8 characters'}, status=400)

    if not request.user.check_password(current_password):
        return JsonResponse({'error': 'Current password is incorrect'}, status=401)

    request.user.set_password(new_password)
    request.user.save()
    update_session_auth_hash(request, request.user)
    return JsonResponse({'success': True, 'message': 'Password changed successfully'})



@csrf_exempt
@login_required
def mobile_staff_set_password(request):
    """POST {user_id, new_password} -> set a user's password (staff only, no old password)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    profile = request.user.profile
    if profile.role not in ('physician', 'admin', 'nurse', 'secretary', 'mid-level'):
        return JsonResponse({'error': 'Staff only'}, status=403)

    body = _parse_body(request)
    user_id = body.get('user_id')
    new_password = body.get('new_password', '')

    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)
    if len(new_password) < 8:
        return JsonResponse({'error': 'New password must be at least 8 characters'}, status=400)

    from django.contrib.auth.models import User
    try:
        target_user = User.objects.get(id=int(user_id))
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    target_user.set_password(new_password)
    target_user.save()
    return JsonResponse({'success': True, 'message': 'Password updated'})


@csrf_exempt
@login_required
def mobile_update_user(request, user_id):
    """PATCH/POST {first_name?, last_name?, email?, phone?, sex?, summary?,
    date_of_birth?, credentials?, npi_number?, practice_*?} for a user.

    Self-only unless caller is admin. Mirrors fields used by the iOS
    SettingsView Profile + Practice tabs. iOS has been calling this URL
    (`/api/user/<id>/update/`) for a while via AuthService.updateUserProfile,
    but the endpoint never actually existed server-side — error was silently
    swallowed (see AuthService.swift:291). Creating it here fixes that latent
    bug AND delivers the new provider/practice fields in one stroke.
    """
    if request.method not in ('PATCH', 'POST'):
        return JsonResponse({'error': 'PATCH required'}, status=405)

    try:
        target_user_id = int(user_id)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid user_id'}, status=400)

    # Self-only OR admin.
    is_self = (request.user.id == target_user_id)
    is_admin = False
    try:
        is_admin = request.user.profile.role == 'admin'
    except (UserProfile.DoesNotExist, AttributeError):
        pass
    if not (is_self or is_admin):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    from django.contrib.auth.models import User
    try:
        target_user = User.objects.get(id=target_user_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    body = _parse_body(request)

    # User table fields.
    if 'first_name' in body:
        target_user.first_name = body['first_name'] or ''
    if 'last_name' in body:
        target_user.last_name = body['last_name'] or ''
    if 'email' in body:
        target_user.email = body['email'] or ''
    target_user.save()

    # UserProfile fields.
    if 'phone' in body:
        profile.phone_number = body['phone'] or ''
    if 'phone_number' in body:
        profile.phone_number = body['phone_number'] or ''
    if 'sex' in body:
        profile.sex = body['sex'] or ''
    if 'summary' in body:
        profile.summary = body['summary'] or ''
    if 'date_of_birth' in body:
        from django.utils.dateparse import parse_datetime, parse_date
        raw = body['date_of_birth']
        if raw:
            parsed = parse_datetime(raw) or parse_date(raw)
            profile.date_of_birth = parsed
        else:
            profile.date_of_birth = None

    # Provider identity (physicians populate; others typically blank).
    if 'credentials' in body:
        profile.credentials = body['credentials'] or ''
    if 'npi_number' in body:
        profile.npi_number = body['npi_number'] or ''

    # Practice block.
    for key in (
        'practice_name', 'practice_street_address', 'practice_city',
        'practice_state', 'practice_zip', 'practice_phone', 'practice_fax',
    ):
        if key in body:
            setattr(profile, key, body[key] or '')

    profile.save()

    return JsonResponse({'success': True, 'user': _user_dict(target_user, profile)})


@csrf_exempt
@login_required
def mobile_upload_signature(request, user_id):
    """POST multipart {file} -> stores the signature PNG on the user's
    profile. Self-only (no admin override — signatures are personal).

    Overwrites any prior signature. No client_uuid required because the
    field is single-slot (not append-only like documents).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        target_user_id = int(user_id)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Invalid user_id'}, status=400)

    # Hard self-only — medico-legal. A staff member must not be able to
    # upload another user's signature via path-parameter manipulation.
    if request.user.id != target_user_id:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    sig_file = request.FILES.get('file')
    if not sig_file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    profile.signature_image = sig_file
    profile.save()

    return JsonResponse({'success': True, 'user': _user_dict(request.user, profile)})


def _assert_signature_accessible(viewer, target_user_id):
    """Returns True if `viewer` is allowed to fetch `target_user_id`'s
    signature image. Self, admin, or a member of a PhysicianTeam where
    target is the physician. Covers: nurses/secretaries/mid-levels printing
    on behalf of their supervising physician.
    """
    try:
        target_user_id = int(target_user_id)
    except (TypeError, ValueError):
        return False

    if viewer.id == target_user_id:
        return True

    try:
        role = viewer.profile.role
    except (UserProfile.DoesNotExist, AttributeError):
        return False

    if role == 'admin':
        return True

    return PhysicianTeam.objects.filter(
        physician_id=target_user_id,
        member=viewer,
    ).exists()


@csrf_exempt
@login_required
def mobile_signature_file(request, user_id):
    """GET -> stream the user's signature_image. Gated by
    `_assert_signature_accessible`. Uniform 404 on deny so callers can't
    probe team membership.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    if not _assert_signature_accessible(request.user, user_id):
        return JsonResponse({'error': 'Signature not found'}, status=404)

    from django.contrib.auth.models import User
    try:
        target_user = User.objects.get(id=int(user_id))
    except User.DoesNotExist:
        return JsonResponse({'error': 'Signature not found'}, status=404)

    try:
        profile = target_user.profile
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'Signature not found'}, status=404)

    if not profile.signature_image or not profile.signature_image.name:
        return JsonResponse({'error': 'Signature not found'}, status=404)

    from django.http import FileResponse
    try:
        return FileResponse(profile.signature_image.open('rb'), content_type='image/png')
    except Exception:
        return JsonResponse({'error': 'Signature not found'}, status=404)


@csrf_exempt
@login_required
def mobile_toggle_patient_active(request):
    """POST {user_id, is_active} -> set user.is_active (staff only)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    profile = request.user.profile
    if profile.role not in ('physician', 'admin', 'nurse', 'secretary', 'mid-level'):
        return JsonResponse({'error': 'Staff only'}, status=403)

    body = _parse_body(request)
    user_id = body.get('user_id')
    is_active = body.get('is_active')

    if user_id is None or is_active is None:
        return JsonResponse({'error': 'user_id and is_active are required'}, status=400)

    from django.contrib.auth.models import User
    try:
        target_user = User.objects.get(id=int(user_id))
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    target_user.is_active = bool(is_active)
    target_user.save()
    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_patients(request):
    """GET -> list of patients for the logged-in physician/staff."""
    user_profile = request.user.profile
    role = user_profile.role

    pc_qs = PatientController.objects.none()

    if role == 'admin':
        patients = UserProfile.objects.filter(role='patient')
        patient_user_ids = [p.user_id for p in patients]
        pc_qs = PatientController.objects.filter(patient_id__in=patient_user_ids)
    elif role == 'physician':
        pc_qs = PatientController.objects.filter(physician=request.user)
        patient_user_ids = [pc.patient_id for pc in pc_qs]
    elif role in ('secretary', 'mid-level', 'nurse'):
        team_members = PhysicianTeam.objects.filter(member=request.user)
        physician_ids = [tm.physician_id for tm in team_members]
        pc_qs = PatientController.objects.filter(physician_id__in=physician_ids)
        patient_user_ids = [pc.patient_id for pc in pc_qs]
    elif role == 'patient':
        patient_user_ids = [request.user.id]
    else:
        patient_user_ids = []

    from django.contrib.auth.models import User
    from django.db.models import Count
    from apps.emr.models import Problem, Todo

    problems_counts = dict(
        Problem.objects.filter(
            patient_id__in=patient_user_ids, is_active=True
        ).values('patient_id').annotate(c=Count('id')).values_list('patient_id', 'c')
    )
    todos_counts = dict(
        Todo.objects.filter(
            patient_id__in=patient_user_ids, accomplished=False
        ).values('patient_id').annotate(c=Count('id')).values_list('patient_id', 'c')
    )

    patients = User.objects.filter(id__in=patient_user_ids).select_related('profile')

    result = []
    for u in patients:
        d = _user_dict(u)
        d['problem_count'] = problems_counts.get(u.id, 0)
        d['todo_count'] = todos_counts.get(u.id, 0)
        result.append(d)

    pc_list = [
        {'id': pc.id, 'patient_id': pc.patient_id, 'physician_id': pc.physician_id}
        for pc in pc_qs
    ]

    return JsonResponse({'success': True, 'patients': result, 'patient_controllers': pc_list})


@csrf_exempt
@login_required
def mobile_team(request):
    """GET -> list of staff members on the logged-in user's care team."""
    from django.contrib.auth.models import User

    user_profile = request.user.profile
    role = user_profile.role

    staff_user_ids = set()

    if role == 'admin':
        staff_profiles = UserProfile.objects.filter(
            role__in=['physician', 'mid-level', 'nurse', 'secretary'],
            user__is_active=True,
        )
        staff_user_ids = {p.user_id for p in staff_profiles}
    elif role == 'physician':
        staff_user_ids.add(request.user.id)
        for tm in PhysicianTeam.objects.filter(physician=request.user):
            staff_user_ids.add(tm.member_id)
    elif role in ('secretary', 'mid-level', 'nurse'):
        staff_user_ids.add(request.user.id)
        team_links = PhysicianTeam.objects.filter(member=request.user)
        physician_ids = [tm.physician_id for tm in team_links]
        staff_user_ids.update(physician_ids)
        for tm in PhysicianTeam.objects.filter(physician_id__in=physician_ids):
            staff_user_ids.add(tm.member_id)

    staff_users = User.objects.filter(id__in=staff_user_ids, is_active=True).select_related('profile')
    result = [_user_dict(u) for u in staff_users]

    # Include PhysicianTeam relationship records so the app can build local links
    relevant_links = PhysicianTeam.objects.filter(
        physician_id__in=staff_user_ids,
        member_id__in=staff_user_ids,
    )
    links = [
        {'id': tm.id, 'physician_id': tm.physician_id, 'member_id': tm.member_id}
        for tm in relevant_links
    ]

    labels_qs = Label.objects.filter(
        Q(is_all=True) | (Q(is_all=False) & Q(author=request.user))
    ).select_related('author')
    label_list = []
    for lbl in labels_qs:
        label_list.append({
            'id': lbl.id,
            'name': lbl.name or '',
            'css_class': lbl.css_class or '',
            'is_all': lbl.is_all,
            'author_id': lbl.author_id,
        })

    return JsonResponse({'success': True, 'team': result, 'team_links': links, 'labels': label_list})


@csrf_exempt
@login_required
def mobile_team_assignments(request):
    """GET -> physician's direct team assignments grouped by role.
    Returns assignments (with PhysicianTeam IDs) and available staff."""
    from django.contrib.auth.models import User

    user_profile = request.user.profile
    role = user_profile.role

    if role not in ('physician', 'admin'):
        return JsonResponse({'error': 'Only physicians and admins can manage team assignments'}, status=403)

    if role == 'physician':
        physician = request.user
    else:
        physician_id = request.GET.get('physician_id')
        if physician_id:
            try:
                physician = User.objects.get(id=int(physician_id))
            except User.DoesNotExist:
                return JsonResponse({'error': 'Physician not found'}, status=404)
        else:
            return JsonResponse({'error': 'physician_id required for admin'}, status=400)

    assignments = PhysicianTeam.objects.filter(physician=physician).select_related('member', 'member__profile')
    assigned = []
    for tm in assignments:
        if tm.member and tm.member.is_active:
            d = _user_dict(tm.member)
            d['team_id'] = tm.id
            assigned.append(d)

    assigned_ids = {tm.member_id for tm in assignments}
    assigned_ids.add(physician.id)
    staff_roles = ['nurse', 'mid-level', 'secretary']
    available_profiles = UserProfile.objects.filter(
        role__in=staff_roles,
        user__is_active=True,
    ).exclude(user_id__in=assigned_ids).select_related('user')
    available = [_user_dict(p.user, profile=p) for p in available_profiles]

    return JsonResponse({
        'success': True,
        'physician': _user_dict(physician),
        'assignments': assigned,
        'available': available,
    })


@csrf_exempt
@login_required
def mobile_team_assign(request):
    """POST {user_id} -> assign a staff member to the physician's team."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth.models import User

    user_profile = request.user.profile
    role = user_profile.role

    if role not in ('physician', 'admin'):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    body = _parse_body(request)
    user_id = body.get('user_id')
    physician_id = body.get('physician_id')

    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)

    if role == 'physician':
        physician = request.user
    elif physician_id:
        try:
            physician = User.objects.get(id=int(physician_id))
        except User.DoesNotExist:
            return JsonResponse({'error': 'Physician not found'}, status=404)
    else:
        return JsonResponse({'error': 'physician_id required for admin'}, status=400)

    try:
        member = User.objects.get(id=int(user_id))
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    tm, created = PhysicianTeam.objects.get_or_create(physician=physician, member=member)
    return JsonResponse({'success': True, 'id': tm.id, 'created': created})


@csrf_exempt
@login_required
def mobile_team_unassign(request):
    """POST {user_id} -> remove a staff member from the physician's team."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth.models import User

    user_profile = request.user.profile
    role = user_profile.role

    if role not in ('physician', 'admin'):
        return JsonResponse({'error': 'Forbidden'}, status=403)

    body = _parse_body(request)
    user_id = body.get('user_id')
    physician_id = body.get('physician_id')

    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)

    if role == 'physician':
        physician = request.user
    elif physician_id:
        try:
            physician = User.objects.get(id=int(physician_id))
        except User.DoesNotExist:
            return JsonResponse({'error': 'Physician not found'}, status=404)
    else:
        return JsonResponse({'error': 'physician_id required for admin'}, status=400)

    deleted, _ = PhysicianTeam.objects.filter(physician=physician, member_id=int(user_id)).delete()
    if deleted == 0:
        return JsonResponse({'error': 'Assignment not found'}, status=404)
    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_patient_full(request, patient_id):
    """GET -> full patient data: problems, notes, labels, todos, observations."""
    import traceback as tb
    from django.contrib.auth.models import User

    try:
        return _mobile_patient_full_inner(request, patient_id)
    except Exception:
        return JsonResponse({
            'success': False,
            'error': tb.format_exc(),
        }, status=500)


def _mobile_patient_full_inner(request, patient_id):
    from django.contrib.auth.models import User
    from django.utils.dateparse import parse_datetime

    try:
        patient_user = User.objects.select_related('profile').get(id=patient_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    since_str = request.GET.get('since')
    since = parse_datetime(since_str) if since_str else None

    max_obs_values = 100
    max_values_str = request.GET.get('max_obs_values')
    if max_values_str:
        try:
            max_obs_values = int(max_values_str)
        except ValueError:
            pass

    sections_str = request.GET.get('sections', '')
    requested_sections = set(sections_str.split(',')) if sections_str else set()

    # Patient info
    patient = _user_dict(patient_user)

    # Problems — always included (core data)
    problems = []
    problem_qs = Problem.objects.filter(patient=patient_user).order_by('id')
    for p in problem_qs:
        problem_dict = {
            'id': p.id,
            'problem_name': p.problem_name or '',
            'concept_id': p.concept_id or '',
            'is_controlled': p.is_controlled,
            'is_active': p.is_active,
            'authenticated': p.authenticated,
            'start_date': p.start_date.isoformat() if p.start_date else None,
            'old_problem_name': p.old_problem_name or '',
        }

        # Notes for this problem
        notes = []
        for n in ProblemNote.objects.filter(problem=p).order_by('-created_on'):
            notes.append({
                'id': n.id,
                'note': n.note or '',
                'note_type': n.note_type or 'wiki',
                'author_id': n.author_id if n.author_id else None,
                'author_name': n.author.get_full_name() if n.author else '',
                'created_on': n.created_on.isoformat() if n.created_on else None,
            })
        problem_dict['notes'] = notes

        # Labels for this problem
        labels = []
        for lbl in p.labels.all():
            labels.append({
                'id': lbl.id,
                'name': lbl.name or '',
                'css_class': lbl.css_class or '',
            })
        problem_dict['labels'] = labels

        # Images for this problem (PR-2). Binary fetched lazily by the
        # client via `mobile_image_file` — only metadata + the proxy URL
        # ride inline so a 30-image problem doesn't balloon the JSON.
        images = []
        for pi in PatientImage.objects.filter(problem=p).order_by('-datetime'):
            images.append({
                'id': pi.id,
                'file_name': pi.file_name or (
                    os.path.basename(pi.image.name) if pi.image else ''
                ),
                'caption': pi.caption or '',
                'image_width': pi.image_width,
                'image_height': pi.image_height,
                'created_on': pi.datetime.isoformat() if pi.datetime else None,
                'author_id': pi.author_id,
                'author_name': pi.author.get_full_name() if pi.author else '',
                'image_url': '/api/media/image/{0}'.format(pi.id),
            })
        problem_dict['images'] = images

        problems.append(problem_dict)

    # Problem relationships — always included
    relationships = []
    problem_ids = [p['id'] for p in problems]
    for rel in ProblemRelationship.objects.filter(source_id__in=problem_ids):
        relationships.append({
            'id': rel.id,
            'source_id': rel.source_id,
            'target_id': rel.target_id,
        })

    # Todos — always included (core data)
    todos = []
    for t in ToDo.objects.filter(patient=patient_user).order_by('order'):
        members = []
        for tto in TaggedToDoOrder.objects.filter(todo=t).select_related('user', 'user__profile'):
            members.append({
                'id': tto.id,
                'user_id': tto.user_id,
                'username': tto.user.username if tto.user else '',
                'user_name': tto.user.get_full_name() if tto.user else '',
                'role': tto.user.profile.role if tto.user else '',
                'status': tto.status,
                'created_on': tto.created_on.isoformat() if tto.created_on else None,
            })
        todos.append({
            'id': t.id,
            'todo': t.todo or '',
            'accomplished': t.accomplished,
            'accomplished_at': t.accomplished_at.isoformat() if t.accomplished_at else None,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'problem_id': t.problem_id if t.problem_id else None,
            'order': t.order,
            'created_on': t.created_on.isoformat() if t.created_on else None,
            'labels': [{'id': l.id, 'name': l.name or '', 'css_class': l.css_class or ''} for l in t.labels.all()],
            'comments': [{
                'id': c.id,
                'comment': c.comment or '',
                'user_id': c.user_id,
                'user_name': c.user.get_full_name() if c.user else '',
                'datetime': c.datetime.isoformat() if c.datetime else None,
            } for c in t.comments.order_by('-datetime')],
            'members': members,
        })

    # Observations — included if no sections filter or 'observations' requested
    observations = []
    if not requested_sections or 'observations' in requested_sections:
        for obs in Observation.objects.filter(subject=patient_user):
            components = []
            for comp in ObservationComponent.objects.filter(observation=obs):
                values_qs = ObservationValue.objects.filter(component=comp).order_by('-effective_datetime')[:max_obs_values]
                values = []
                for val in values_qs:
                    values.append({
                        'id': val.id,
                        'value_quantity': str(val.value_quantity) if val.value_quantity is not None else None,
                        'effective_datetime': val.effective_datetime.isoformat() if val.effective_datetime else None,
                        'author_name': val.author.get_full_name() if val.author else '',
                    })
                components.append({
                    'id': comp.id,
                    'name': comp.name or '',
                    'component_code': comp.component_code or '',
                    'values': values,
                })

            # Get unit from observation_units
            unit = ''
            obs_units = obs.observation_units.filter(is_used=True).first()
            if obs_units:
                unit = obs_units.value_unit or ''

            observations.append({
                'id': obs.id,
                'name': obs.name or '',
                'code': obs.code or '',
                'color': obs.color or '',
                'graph': obs.graph or 'Line',
                'comments': obs.comments or '',
                'unit': unit,
                'components': components,
            })

    # Observation pins to problems
    pins = []
    if not requested_sections or 'observations' in requested_sections:
        obs_ids = [o['id'] for o in observations]
        for pin in ObservationPinToProblem.objects.filter(observation_id__in=obs_ids):
            pins.append({
                'id': pin.id,
                'observation_id': pin.observation_id,
                'problem_id': pin.problem_id,
            })

    # Encounters — included if no sections filter or 'encounters' requested
    encounters = []
    if not requested_sections or 'encounters' in requested_sections:
        encounter_qs = (
            Encounter.objects.filter(patient=patient_user)
            .select_related('physician')
            .prefetch_related(
                'encounter_events',
                'encounter_problem_records',
                'encounter_todo_records',
                'encounterobservationvalue_set',
            )
            .order_by('-starttime')
        )
        if since:
            encounter_qs = encounter_qs.filter(starttime__gte=since)

        for enc in encounter_qs:
            events = []
            for ev in enc.encounter_events.order_by('datetime'):
                offset_seconds = max(0, int((ev.datetime - enc.starttime).total_seconds()))
                offset_minutes = offset_seconds // 60
                offset_secs = offset_seconds % 60

                events.append({
                    'id': ev.id,
                    'client_uuid': str(ev.client_uuid) if ev.client_uuid else None,
                    'datetime': ev.datetime.isoformat(),
                    'summary': _strip_html(ev.summary),
                    'offset_string': f"{offset_minutes:02d}:{offset_secs:02d}",
                    'is_favorite': ev.is_favorite,
                    'favorite_name': ev.name_favorite or '',
                })

            enc_problem_ids = [
                r.problem_id for r in enc.encounter_problem_records.all()
            ]
            enc_todo_ids = [
                r.todo_id for r in enc.encounter_todo_records.all()
            ]
            enc_obs_value_ids = [
                r.observation_value_id for r in enc.encounterobservationvalue_set.all()
            ]

            physician_name = ''
            if enc.physician:
                physician_name = enc.physician.get_full_name() or enc.physician.username

            encounters.append({
                'id': enc.id,
                'client_uuid': str(enc.client_uuid) if enc.client_uuid else None,
                'physician_id': enc.physician_id,
                'physician_name': physician_name,
                'start_time': enc.starttime.isoformat(),
                'stop_time': enc.stoptime.isoformat() if enc.stoptime else None,
                'audio_path': str(enc.audio) if enc.audio else '',
                'note': enc.note or '',
                'transcript': enc.transcript or '',
                'recorder_status': enc.recorder_status,
                'events': events,
                'problem_ids': enc_problem_ids,
                'todo_ids': enc_todo_ids,
                'observation_value_ids': enc_obs_value_ids,
            })

    # Documents — included if no sections filter or 'documents' requested
    documents = []
    if not requested_sections or 'documents' in requested_sections:
        for doc in Document.objects.filter(patient=patient_user).select_related('author').prefetch_related('labels'):
            doc_size = 0
            if doc.document:
                try:
                    doc_size = doc.document.size
                except Exception:
                    pass

            author_name = ''
            if doc.author:
                author_name = doc.author.get_full_name() or doc.author.username

            doc_problem_ids = list(
                DocumentProblem.objects.filter(document=doc).values_list('problem_id', flat=True)
            )
            doc_todo_ids = list(
                DocumentTodo.objects.filter(document=doc).values_list('todo_id', flat=True)
            )

            doc_labels = [{'id': l.id, 'name': l.name or '', 'css_class': l.css_class or ''} for l in doc.labels.all()]

            documents.append({
                'id': doc.id,
                'document_name': doc.document_name or '',
                'file_name': doc.filename() if doc.document else '',
                'file_extension': doc.file_extension_lower() if doc.document else '',
                'mime_type': doc.file_mime_type() if doc.document else '',
                'file_size': doc_size,
                'file_path': str(doc.document) if doc.document else '',
                'author_name': author_name,
                'created_on': doc.created_on.isoformat() if doc.created_on else None,
                'problem_ids': doc_problem_ids,
                'todo_ids': doc_todo_ids,
                'labels': doc_labels,
            })

    # Activity logs
    problem_activities = []
    for pa in ProblemActivity.objects.filter(problem_id__in=problem_ids).select_related('author').order_by('-created_on'):
        problem_activities.append({
            'id': pa.id,
            'problem_id': pa.problem_id,
            'author_name': pa.author.get_full_name() if pa.author else '',
            'activity': pa.activity or '',
            'is_input_type': pa.is_input_type,
            'is_output_type': pa.is_output_type,
            'created_on': pa.created_on.isoformat() if pa.created_on else None,
        })

    todo_ids_list = [t['id'] for t in todos]
    todo_activities = []
    for ta in TodoActivity.objects.filter(todo_id__in=todo_ids_list).select_related('author').order_by('-created_on'):
        todo_activities.append({
            'id': ta.id,
            'todo_id': ta.todo_id,
            'author_name': ta.author.get_full_name() if ta.author else '',
            'activity': ta.activity or '',
            'created_on': ta.created_on.isoformat() if ta.created_on else None,
        })

    return JsonResponse({
        'success': True,
        'patient': patient,
        'problems': problems,
        'relationships': relationships,
        'todos': todos,
        'observations': observations,
        'observation_pins': pins,
        'encounters': encounters,
        'documents': documents,
        'problem_activities': problem_activities,
        'todo_activities': todo_activities,
    })


@csrf_exempt
@login_required
def mobile_encounter_audio(request, encounter_id):
    """GET -> stream the audio file for an encounter.

    PR-2 (2026-06-08) added the `_assert_patient_access` gate. Before this
    patch, any authenticated user could fetch any encounter's audio by
    guessing the ID (classic IDOR — PHI leak). The gate matches the
    role-by-role visibility in `mobile_patients`. Do NOT remove without
    coordinating with the PHI policy in CLAUDE.md.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    try:
        enc = Encounter.objects.get(id=encounter_id)
    except Encounter.DoesNotExist:
        return JsonResponse({'error': 'Encounter not found'}, status=404)

    if not _assert_patient_access(request.user, enc.patient_id):
        # Uniform 404 — don't leak the encounter's existence to an
        # unauthorized caller.
        return JsonResponse({'error': 'Encounter not found'}, status=404)

    if not enc.audio:
        return JsonResponse({'error': 'No audio file'}, status=404)

    mime_type, _ = mimetypes.guess_type(enc.audio.name)
    response = FileResponse(
        enc.audio.open('rb'),
        content_type=mime_type or 'audio/mpeg',
    )
    response['Content-Length'] = enc.audio.size
    response['Content-Disposition'] = (
        'inline; filename="%s"' % os.path.basename(enc.audio.name)
    )
    return response


@csrf_exempt
@login_required
def mobile_document_file(request, document_id):
    """GET -> stream the file for a document.

    PR-2 (2026-06-08) added the `_assert_patient_access` gate AND an
    explicit deny for orphaned documents (patient=None). Before this
    patch, any authenticated user could fetch any document's binary by
    guessing the ID. Orphan policy is "fail closed" per the PHI policy
    in CLAUDE.md — if the document has no patient context, no provider
    can prove a clinical right to view it.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

    # If it's assigned to a patient, assert patient access.
    # If it's an unassigned document (patient=None, team!=None), assert team access.
    # Otherwise (true orphan), deny.
    if doc.patient_id is not None:
        if not _assert_patient_access(request.user, doc.patient_id):
            return JsonResponse({'error': 'Document not found'}, status=404)
    elif doc.team_id is not None:
        if not _assert_team_access(request.user, doc.team_id):
            return JsonResponse({'error': 'Document not found'}, status=404)
    else:
        return JsonResponse({'error': 'Document not found'}, status=404)

    if not doc.document:
        return JsonResponse({'error': 'No file attached'}, status=404)

    mime_type = doc.file_mime_type() or 'application/octet-stream'
    response = FileResponse(
        doc.document.open('rb'),
        content_type=mime_type,
    )
    response['Content-Length'] = doc.document.size
    response['Content-Disposition'] = (
        'inline; filename="%s"' % doc.filename()
    )
    return response


@csrf_exempt
@login_required
def mobile_image_file(request, image_id):
    """GET -> stream the binary for a PatientImage.

    New in PR-2 (2026-06-08). Gated by `_assert_patient_access` from the
    start — clinical photos are PHI and the previous audio/document proxies
    leaking by missing RBAC is exactly the trap we're not repeating here.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    try:
        img = PatientImage.objects.get(id=image_id)
    except PatientImage.DoesNotExist:
        return JsonResponse({'error': 'Image not found'}, status=404)

    if not _assert_patient_access(request.user, img.patient_id):
        # Uniform 404 with the not-found path so callers can't enumerate
        # other clinics' image IDs.
        return JsonResponse({'error': 'Image not found'}, status=404)

    if not img.image:
        return JsonResponse({'error': 'No image file'}, status=404)

    mime_type, _ = mimetypes.guess_type(img.image.name)
    response = FileResponse(
        img.image.open('rb'),
        content_type=mime_type or 'image/jpeg',
    )
    response['Content-Length'] = img.image.size
    response['Content-Disposition'] = (
        'inline; filename="%s"' % os.path.basename(img.image.name)
    )
    return response


def _apply_encounter_relationships_and_events(encounter, body):
    """Apply problem_ids, todo_ids, observation_value_ids, events from body to encounter.

    Defensive partial semantics: only acts on keys PRESENT in body. Absent keys
    preserve existing state — protects against future clients that send a partial
    payload from accidentally wiping the encounter's relationships.

    Relationships use replace-by-snapshot: present key clears existing rows for
    THIS encounter and recreates from the list. iOS always sends the full set.

    Events use update_or_create keyed on client_uuid for idempotent retry. Returns
    a list of {sync_id, id} dicts for every event the body touched (new or
    updated), so iOS can map server IDs back to its local EncounterEvent rows.
    """
    from django.utils.dateparse import parse_datetime

    event_mappings = []

    if 'problem_ids' in body:
        problem_ids = [int(pid) for pid in body['problem_ids'] or []]
        EncounterProblemRecord.objects.filter(encounter=encounter).delete()
        if problem_ids:
            EncounterProblemRecord.objects.bulk_create([
                EncounterProblemRecord(encounter=encounter, problem_id=pid)
                for pid in problem_ids
            ])

    if 'todo_ids' in body:
        todo_ids = [int(tid) for tid in body['todo_ids'] or []]
        EncounterTodoRecord.objects.filter(encounter=encounter).delete()
        if todo_ids:
            EncounterTodoRecord.objects.bulk_create([
                EncounterTodoRecord(encounter=encounter, todo_id=tid)
                for tid in todo_ids
            ])

    if 'observation_value_ids' in body:
        ov_ids = [int(vid) for vid in body['observation_value_ids'] or []]
        EncounterObservationValue.objects.filter(encounter=encounter).delete()
        if ov_ids:
            EncounterObservationValue.objects.bulk_create([
                EncounterObservationValue(encounter=encounter, observation_value_id=vid)
                for vid in ov_ids
            ])

    if 'events' in body:
        for event_data in body['events'] or []:
            client_uuid = event_data.get('client_uuid')
            if not client_uuid:
                # Events without a client_uuid can't be safely deduped on retry,
                # so we skip them. iOS always sets syncID at init.
                continue
            defaults = {
                'encounter': encounter,
                'summary': event_data.get('summary', '') or '',
                'is_favorite': bool(event_data.get('is_favorite', False)),
                'name_favorite': event_data.get('favorite_name'),
            }
            dt_str = event_data.get('datetime')
            parsed_dt = parse_datetime(dt_str) if dt_str else None
            if parsed_dt:
                defaults['timestamp'] = parsed_dt
            ev, _ = EncounterEvent.objects.update_or_create(
                client_uuid=client_uuid,
                defaults=defaults,
            )
            # Override the model's auto_now_add `datetime` field with the
            # client's actual event-creation time. Without this, every event
            # in a single PATCH batch gets stamped with near-identical server
            # times, and the serializer's offset_string computation
            # (datetime - encounter.starttime) collapses to the same value
            # for every event in the batch.
            if parsed_dt:
                EncounterEvent.objects.filter(id=ev.id).update(datetime=parsed_dt)
            event_mappings.append({'sync_id': str(client_uuid), 'id': ev.id})

    return event_mappings


@csrf_exempt
@login_required
@transaction.atomic
def mobile_upload_encounter_audio(request, patient_id):
    """POST multipart: create-or-find Encounter by client_uuid, upload audio file.

    Idempotent: a retry with the same client_uuid updates the existing row
    rather than creating a duplicate. Also accepts relationship + events fields
    via form-data for clients that bundle everything in the upload (iOS
    currently sends them via the follow-up PATCH; this is here for future use).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth.models import User
    from django.utils.dateparse import parse_datetime

    try:
        patient_user = User.objects.get(id=patient_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    audio_file = request.FILES.get('file')
    if not audio_file:
        return JsonResponse({'error': 'No audio file provided'}, status=400)

    client_uuid = request.POST.get('client_uuid') or None
    note = request.POST.get('note', '')
    recorder_status = int(request.POST.get('recorder_status', 2))

    defaults = {
        'physician': request.user,
        'patient': patient_user,
        'audio': audio_file,
        'note': note,
        'recorder_status': recorder_status,
    }
    stop_time = request.POST.get('stop_time')
    if stop_time:
        defaults['stoptime'] = parse_datetime(stop_time)

    if client_uuid:
        enc, _ = Encounter.objects.update_or_create(
            client_uuid=client_uuid,
            defaults=defaults,
        )
    else:
        # Legacy clients without client_uuid still get a fresh row.
        enc = Encounter.objects.create(**defaults)

    start_time = request.POST.get('start_time')
    if start_time:
        parsed = parse_datetime(start_time)
        if parsed:
            Encounter.objects.filter(id=enc.id).update(starttime=parsed)

    return JsonResponse({'success': True, 'id': enc.id})


@csrf_exempt
@login_required
@transaction.atomic
def mobile_create_encounter(request, patient_id):
    """POST {client_uuid?, start_time?, stop_time?, note?, transcript?,
    recorder_status?, problem_ids?, todo_ids?, observation_value_ids?, events?}
    -> create-or-find text-only Encounter.

    Audio-bearing encounters use mobile_upload_encounter_audio. This is the
    text-only / events-only path for when iOS has audio recording disabled.
    Idempotent via client_uuid. Events are matched + deduped by their own
    client_uuid; response includes the sync_id → server_id mapping so iOS can
    set EncounterEvent.remoteID locally.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth.models import User
    from django.utils.dateparse import parse_datetime

    try:
        patient_user = User.objects.get(id=patient_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    body = _parse_body(request)
    client_uuid = body.get('client_uuid') or None

    defaults = {
        'physician': request.user,
        'patient': patient_user,
        'note': body.get('note', '') or '',
        'transcript': body.get('transcript', '') or '',
        'recorder_status': int(body.get('recorder_status', 2)),
    }
    stop_time = body.get('stop_time')
    if stop_time:
        defaults['stoptime'] = parse_datetime(stop_time)

    if client_uuid:
        enc, _ = Encounter.objects.update_or_create(
            client_uuid=client_uuid,
            defaults=defaults,
        )
    else:
        enc = Encounter.objects.create(**defaults)

    start_time = body.get('start_time')
    if start_time:
        parsed = parse_datetime(start_time)
        if parsed:
            Encounter.objects.filter(id=enc.id).update(starttime=parsed)

    event_mappings = _apply_encounter_relationships_and_events(enc, body)

    return JsonResponse({'success': True, 'id': enc.id, 'events': event_mappings})


@csrf_exempt
@login_required
@transaction.atomic
def mobile_update_encounter(request, patient_id, encounter_id):
    """PATCH {note?, transcript?, recorder_status?, stop_time?, problem_ids?,
    todo_ids?, observation_value_ids?, events?} — partial update.

    Defensive partial semantics: only keys PRESENT in the body are applied.
    Absent relationship keys preserve existing rows (so omitting problem_ids
    does NOT wipe linked problems). Events: each is upserted by client_uuid;
    response carries the sync_id → server_id mapping for new events.
    """
    if request.method not in ('PATCH', 'POST'):
        return JsonResponse({'error': 'PATCH required'}, status=405)

    try:
        enc = Encounter.objects.get(id=encounter_id, patient_id=patient_id)
    except Encounter.DoesNotExist:
        return JsonResponse({'error': 'Encounter not found'}, status=404)

    from django.utils.dateparse import parse_datetime

    body = _parse_body(request)
    if 'note' in body:
        enc.note = body['note'] or ''
    if 'transcript' in body:
        enc.transcript = body['transcript'] or ''
    if 'recorder_status' in body and body['recorder_status'] is not None:
        enc.recorder_status = int(body['recorder_status'])
    if 'stop_time' in body:
        enc.stoptime = parse_datetime(body['stop_time']) if body['stop_time'] else None
    enc.save()

    event_mappings = _apply_encounter_relationships_and_events(enc, body)

    return JsonResponse({'success': True, 'events': event_mappings})


@csrf_exempt
@login_required
def mobile_upload_document(request, patient_id):
    """POST multipart: create document record + upload file.

    PR-4 (2026-06-08) added the `_assert_patient_access` gate. Before this
    patch, any authenticated user could upload to any patient by guessing the
    id (same IDOR family as the audio/document/image read proxies — closed
    in PR-2 SEC-FIX `f0be8d93`). Do NOT remove without coordinating with the
    PHI policy in CLAUDE.md.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not _assert_patient_access(request.user, patient_id):
        # Uniform 404 — don't leak the patient's existence to an unauthorized
        # caller (same shape as the read proxies).
        return JsonResponse({'error': 'Patient not found'}, status=404)

    from django.contrib.auth.models import User

    try:
        patient_user = User.objects.get(id=patient_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    doc_file = request.FILES.get('file')
    if not doc_file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    client_uuid = request.POST.get('client_uuid')
    if not client_uuid:
        # Required so retries can no-op rather than create duplicate rows.
        # Matches the contract from mobile_upload_encounter_audio and
        # mobile_upload_problem_image (PR-2). Pre-PR-4 clients that don't
        # send this will start failing — coordinated with the iOS rollout
        # of the matching `Document.syncID.uuidString` body field.
        return JsonResponse({'error': 'client_uuid is required'}, status=400)

    document_name = request.POST.get('document_name', doc_file.name)

    doc, created = Document.objects.get_or_create(
        client_uuid=client_uuid,
        defaults={
            'document': doc_file,
            'document_name': document_name,
            'author': request.user,
            'patient': patient_user,
        },
    )

    if created:
        # At upload time the document has no DocumentProblem links yet
        # (link POSTs come from iOS afterwards). The audit fan-out helper
        # falls back to problem=None per the PR-3 / PR-4 routing decision,
        # landing the row on the patient-scope legal trail. Subsequent
        # link / unlink POSTs emit their own per-problem audit rows.
        _emit_document_audit(
            doc, request.user,
            f"Added document: {document_name}"
        )

    return JsonResponse({'success': True, 'id': doc.id, 'created': created})


def _emit_document_audit(document, user, activity):
    """Fan out a ProblemActivity row per problem the document is currently
    linked to. If the document has no problem links (orphaned or freshly
    uploaded), write a single `problem=None` row to maintain the patient-
    scope legal trail.

    Mirrors `_emit_observation_audit` from PR-3 (2026-06-08). The
    nullable-`problem` FK on ProblemActivity (migration `0173`) enables
    the unlinked case. Do NOT add new audit emission paths that bypass
    this helper — they will drift from the global timeline rule.
    """
    links = list(DocumentProblem.objects.filter(document=document).select_related('problem'))
    if links:
        for link in links:
            if link.problem is not None:
                add_problem_activity(link.problem, user, activity)
    else:
        add_problem_activity(None, user, activity)


@csrf_exempt
@login_required
def mobile_delete_document(request, patient_id, document_id):
    """DELETE -> remove a Document + its GCS object + its link rows.

    Idempotent: a retried DELETE after a lost response returns 200 even
    when the row is already gone. Matches the PR-1 / PR-2 / PR-3 contract.
    Audit fan-out reflects the link state at deletion time — clinicians
    who reviewed the document via a specific problem will see the
    `Removed document: <name>` row on that problem's timeline. Orphaned
    documents (no links) land the row on the patient-scope timeline
    (`problem=None`).
    """
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE required'}, status=405)

    if not _assert_patient_access(request.user, patient_id):
        return JsonResponse({'error': 'Document not found'}, status=404)

    try:
        doc = Document.objects.get(id=document_id, patient_id=patient_id)
    except Document.DoesNotExist:
        # Genuinely gone — retry-safe success.
        return JsonResponse({'success': True})

    document_name = doc.document_name or 'document'

    # Snapshot the linked-problem set BEFORE we wipe the rows; the audit
    # fan-out below needs to land on each problem the doc was linked to.
    linked_problems = list(
        DocumentProblem.objects.filter(document=doc).select_related('problem')
    )

    if doc.document:
        # Triggers the django-storages GCS backend delete, removing the
        # binary. Set save=False since we follow with doc.delete() right
        # after.
        doc.document.delete(save=False)
    doc.delete()  # CASCADE wipes DocumentProblem + DocumentTodo rows.

    audit_msg = f"Removed document: {document_name}"
    if linked_problems:
        for link in linked_problems:
            if link.problem is not None:
                add_problem_activity(link.problem, request.user, audit_msg)
    else:
        add_problem_activity(None, request.user, audit_msg)

    return JsonResponse({'success': True})


# ---------------------------------------------------------------------------
# PR-5 (2026-06-11) — Shared unassigned documents pool.
#
# Per-team pool of PDFs awaiting assignment to a patient. Visible to all
# staff users who are members of the team via `PhysicianTeam`. Soft-claim
# concurrency: when a user opens a doc, server stamps `claimed_by` +
# `claimed_at`; auto-expires after `_UNASSIGNED_CLAIM_TTL_SECONDS` of no
# heartbeat (5 min). Heartbeat fires every 60s from the iOS detail view.
#
# On `assign`, the row UPDATEs in place: `patient` ← target, `team` ← NULL,
# `claimed_*` ← NULL. The GCS object stays at `documents/<uuid>.<ext>` (same
# path the standard upload uses) — access control is checked via the DB row,
# not the path.
# ---------------------------------------------------------------------------

_UNASSIGNED_CLAIM_TTL_SECONDS = 300  # 5 minutes
_UNASSIGNED_DOCS_LOGGER = logging.getLogger('smallbrain.unassigned_docs')


def _user_team_ids(user):
    """Returns the set of physician/team ids this user can access for the
    unassigned pool. Mirrors the role table in `_assert_patient_access`."""
    try:
        role = user.profile.role
    except (UserProfile.DoesNotExist, AttributeError):
        return set()

    if role == 'admin':
        # Admins see every team's pool. The list endpoint converts this
        # marker into a no-filter query.
        return None
    elif role == 'physician':
        # A physician IS their own team.
        return {user.id}
    elif role in ('secretary', 'mid-level', 'nurse'):
        return set(
            PhysicianTeam.objects.filter(member=user).values_list('physician_id', flat=True)
        )
    return set()


def _assert_team_access(user, team_id):
    """True if `user` may upload to / claim / assign / delete from team
    `team_id`'s unassigned pool. Same role table as `_assert_patient_access`,
    re-used for the unassigned-pool endpoints."""
    try:
        team_id = int(team_id)
    except (TypeError, ValueError):
        return False

    allowed = _user_team_ids(user)
    if allowed is None:  # admin
        return True
    return team_id in allowed


def _sweep_expired_claims():
    """Clear claims older than the TTL. Run inline on every list query —
    cheap UPDATE with a partial index on `claimed_at IS NOT NULL` would be
    ideal but the table is small enough today that a plain WHERE is fine."""
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(seconds=_UNASSIGNED_CLAIM_TTL_SECONDS)
    Document.objects.filter(
        patient__isnull=True,
        team__isnull=False,
        claimed_at__lt=cutoff,
    ).update(claimed_by=None, claimed_at=None)


def _unassigned_doc_dict(doc):
    """Serialize one unassigned-pool row for the list response. Mirrors the
    snake_case raw-dict pattern from `mobile_patients` etc."""
    return {
        'id': doc.id,
        'client_uuid': str(doc.client_uuid) if doc.client_uuid else None,
        'team_id': doc.team_id,
        'document_name': doc.document_name or '',
        'file_name': os.path.basename(doc.document.name) if doc.document else '',
        'mime_type': doc.file_mime_type(),
        'file_size': doc.document.size if doc.document else 0,
        'author_id': doc.author_id,
        'author_name': (
            f"{doc.author.first_name} {doc.author.last_name}".strip() or doc.author.username
        ) if doc.author_id else '',
        'created_at': doc.created_on.isoformat() if doc.created_on else None,
        'claimed_by_id': doc.claimed_by_id,
        'claimed_by_name': (
            f"{doc.claimed_by.first_name} {doc.claimed_by.last_name}".strip() or doc.claimed_by.username
        ) if doc.claimed_by_id else None,
        'claimed_at': doc.claimed_at.isoformat() if doc.claimed_at else None,
    }


@csrf_exempt
@login_required
def mobile_upload_unassigned_document(request, team_id):
    """POST multipart -> create an unassigned-pool Document scoped to a team.

    Path mirrors `mobile_upload_document` shape: same `client_uuid`
    idempotency, same GCS path scheme (`documents/<uuid>.<ext>` via
    `set_document_path_uuid`). The only difference is `patient` stays NULL
    and `team` is set. Audit emission is deferred to the `assign` endpoint
    — there is no patient timeline to hang a row on while the doc is in
    the pool. Operational log on success for trail visibility.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not _assert_team_access(request.user, team_id):
        return JsonResponse({'error': 'Team not found'}, status=404)

    from django.contrib.auth.models import User

    try:
        team_user = User.objects.get(id=team_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)

    doc_file = request.FILES.get('file')
    if not doc_file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    client_uuid = request.POST.get('client_uuid')
    if not client_uuid:
        return JsonResponse({'error': 'client_uuid is required'}, status=400)

    document_name = request.POST.get('document_name', doc_file.name)

    doc, created = Document.objects.get_or_create(
        client_uuid=client_uuid,
        defaults={
            'document': doc_file,
            'document_name': document_name,
            'author': request.user,
            'patient': None,
            'team': team_user,
        },
    )

    return JsonResponse({'success': True, 'id': doc.id, 'created': created})


@csrf_exempt
@login_required
def mobile_unassigned_documents_list(request):
    """GET -> merged unassigned-pool list across every team the caller is a
    member of. Admins see every team's pool. Sweeps expired claims first
    so the response reflects current claim state without requiring a
    background job."""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    _sweep_expired_claims()

    allowed = _user_team_ids(request.user)
    qs = Document.objects.filter(patient__isnull=True, team__isnull=False)
    if allowed is None:
        pass  # admin: no further filter
    elif not allowed:
        return JsonResponse({'success': True, 'documents': []})
    else:
        qs = qs.filter(team_id__in=allowed)

    qs = qs.select_related('author', 'claimed_by').order_by('-created_on')

    return JsonResponse({
        'success': True,
        'documents': [_unassigned_doc_dict(d) for d in qs],
    })


@csrf_exempt
@login_required
def mobile_unassigned_document_claim(request, document_id):
    """POST -> try to claim an unassigned doc. Returns 409 with the existing
    claimant if held by someone else. Idempotent: re-claiming a doc you
    already hold refreshes `claimed_at` (functionally the same as the
    heartbeat endpoint)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.utils import timezone
    from datetime import timedelta

    with transaction.atomic():
        try:
            # FOR UPDATE serializes concurrent claims on the same row.
            doc = Document.objects.select_for_update().get(
                id=document_id, patient__isnull=True, team__isnull=False,
            )
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        if not _assert_team_access(request.user, doc.team_id):
            return JsonResponse({'error': 'Document not found'}, status=404)

        cutoff = timezone.now() - timedelta(seconds=_UNASSIGNED_CLAIM_TTL_SECONDS)
        held_by_other = (
            doc.claimed_by_id is not None
            and doc.claimed_by_id != request.user.id
            and doc.claimed_at is not None
            and doc.claimed_at >= cutoff
        )
        if held_by_other:
            return JsonResponse({
                'success': False,
                'reason': 'already_claimed',
                'claimed_by_id': doc.claimed_by_id,
                'claimed_by_name': (
                    f"{doc.claimed_by.first_name} {doc.claimed_by.last_name}".strip()
                    or doc.claimed_by.username
                ),
                'claimed_at': doc.claimed_at.isoformat() if doc.claimed_at else None,
            }, status=409)

        doc.claimed_by = request.user
        doc.claimed_at = timezone.now()
        doc.save(update_fields=['claimed_by', 'claimed_at'])

    return JsonResponse({'success': True, 'document': _unassigned_doc_dict(doc)})


@csrf_exempt
@login_required
def mobile_unassigned_document_claim_heartbeat(request, document_id):
    """POST -> refresh `claimed_at` if the caller is the current claimant.
    No-op (returns 409) if someone else holds the claim — the iOS detail
    view will see the 409 and dismiss itself."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.utils import timezone

    with transaction.atomic():
        try:
            doc = Document.objects.select_for_update().get(
                id=document_id, patient__isnull=True, team__isnull=False,
            )
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        if not _assert_team_access(request.user, doc.team_id):
            return JsonResponse({'error': 'Document not found'}, status=404)

        if doc.claimed_by_id != request.user.id:
            return JsonResponse({
                'success': False,
                'reason': 'not_holder',
            }, status=409)

        doc.claimed_at = timezone.now()
        doc.save(update_fields=['claimed_at'])

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_unassigned_document_release(request, document_id):
    """POST -> clear the claim if held by the caller. Idempotent: returns
    success even if the claim has already lapsed or someone else holds it
    (releasing-what-you-don't-hold is a no-op from your perspective)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    with transaction.atomic():
        try:
            doc = Document.objects.select_for_update().get(
                id=document_id, patient__isnull=True, team__isnull=False,
            )
        except Document.DoesNotExist:
            return JsonResponse({'success': True})

        if doc.claimed_by_id == request.user.id:
            doc.claimed_by = None
            doc.claimed_at = None
            doc.save(update_fields=['claimed_by', 'claimed_at'])

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_unassigned_document_assign(request, document_id):
    """POST -> assign an unassigned doc to a patient. Body: `{patient_id,
    document_name?}`. Validates the caller currently holds the claim (or
    that the claim is unheld); validates the caller has access to the
    target patient; UPDATEs the row in place; emits the standard
    `Added document: <name>` audit on the patient timeline."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    target_patient_id = body.get('patient_id')
    if not target_patient_id:
        return JsonResponse({'error': 'patient_id required'}, status=400)

    if not _assert_patient_access(request.user, target_patient_id):
        return JsonResponse({'error': 'Patient not found'}, status=404)

    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta

    try:
        target_patient = User.objects.get(id=target_patient_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    with transaction.atomic():
        try:
            doc = Document.objects.select_for_update().get(
                id=document_id, patient__isnull=True, team__isnull=False,
            )
        except Document.DoesNotExist:
            return JsonResponse({'error': 'Document not found'}, status=404)

        if not _assert_team_access(request.user, doc.team_id):
            return JsonResponse({'error': 'Document not found'}, status=404)

        cutoff = timezone.now() - timedelta(seconds=_UNASSIGNED_CLAIM_TTL_SECONDS)
        held_by_other = (
            doc.claimed_by_id is not None
            and doc.claimed_by_id != request.user.id
            and doc.claimed_at is not None
            and doc.claimed_at >= cutoff
        )
        if held_by_other:
            return JsonResponse({
                'success': False,
                'reason': 'already_claimed',
                'claimed_by_id': doc.claimed_by_id,
            }, status=409)

        new_name = body.get('document_name')
        if new_name:
            doc.document_name = new_name

        doc.patient = target_patient
        doc.team = None
        doc.claimed_by = None
        doc.claimed_at = None
        doc.save(update_fields=[
            'patient', 'team', 'claimed_by', 'claimed_at', 'document_name',
        ])

        _emit_document_audit(
            doc, request.user,
            f"Added document: {doc.document_name or 'document'}",
        )

    _UNASSIGNED_DOCS_LOGGER.info(json.dumps({
        'severity': 'INFO',
        'message': 'unassigned_document_assigned',
        'document_id': doc.id,
        'patient_id': int(target_patient_id),
        'actor_id': request.user.id,
        'serviceContext': {'service': 'smallbrain-api'},
    }))

    return JsonResponse({'success': True, 'id': doc.id})


@csrf_exempt
@login_required
def mobile_unassigned_document_delete(request, document_id):
    """DELETE -> hard-delete an unassigned-pool row + its GCS object.
    Allowed only when the doc is unclaimed or claimed by the caller. No
    patient timeline to audit to — operational log only."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE required'}, status=405)

    from django.utils import timezone
    from datetime import timedelta

    with transaction.atomic():
        try:
            doc = Document.objects.select_for_update().get(
                id=document_id, patient__isnull=True, team__isnull=False,
            )
        except Document.DoesNotExist:
            return JsonResponse({'success': True})

        if not _assert_team_access(request.user, doc.team_id):
            return JsonResponse({'error': 'Document not found'}, status=404)

        cutoff = timezone.now() - timedelta(seconds=_UNASSIGNED_CLAIM_TTL_SECONDS)
        held_by_other = (
            doc.claimed_by_id is not None
            and doc.claimed_by_id != request.user.id
            and doc.claimed_at is not None
            and doc.claimed_at >= cutoff
        )
        if held_by_other:
            return JsonResponse({
                'success': False,
                'reason': 'already_claimed',
            }, status=409)

        snapshot_id = doc.id
        snapshot_team_id = doc.team_id
        if doc.document:
            doc.document.delete(save=False)
        doc.delete()

    _UNASSIGNED_DOCS_LOGGER.info(json.dumps({
        'severity': 'INFO',
        'message': 'unassigned_document_deleted',
        'document_id': snapshot_id,
        'team_id': snapshot_team_id,
        'actor_id': request.user.id,
        'serviceContext': {'service': 'smallbrain-api'},
    }))

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_document_problem_link(request, patient_id, document_id, problem_id):
    """POST -> link a document to a problem; DELETE -> unlink.

    URL-coordinate identity: a link is fully described by (document_id,
    problem_id), so POST is naturally idempotent via `get_or_create`.
    Repeat calls return the same row id with `created=False`. Audit is
    written directly to the target problem (not via the fan-out helper)
    because the action is intrinsically a problem-level annotation.
    """
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'error': 'POST or DELETE required'}, status=405)

    if not _assert_patient_access(request.user, patient_id):
        return JsonResponse({'error': 'Patient not found'}, status=404)

    try:
        doc = Document.objects.get(id=document_id, patient_id=patient_id)
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

    try:
        problem = Problem.objects.get(id=problem_id, patient_id=patient_id)
    except Problem.DoesNotExist:
        return JsonResponse({'error': 'Problem not found'}, status=404)

    document_name = doc.document_name or 'document'

    if request.method == 'DELETE':
        deleted, _ = DocumentProblem.objects.filter(
            document=doc, problem=problem,
        ).delete()
        if deleted:
            add_problem_activity(
                problem, request.user,
                f"Unlinked document: {document_name}"
            )
        return JsonResponse({'success': True})

    # POST -> get_or_create
    link, created = DocumentProblem.objects.get_or_create(
        document=doc, problem=problem,
        defaults={'author': request.user},
    )
    if created:
        add_problem_activity(
            problem, request.user,
            f"Linked document: {document_name}"
        )
    return JsonResponse({'success': True, 'id': link.id, 'created': created})


@csrf_exempt
@login_required
def mobile_document_todo_link(request, patient_id, document_id, todo_id):
    """POST -> link a document to a todo; DELETE -> unlink.

    URL-coordinate identity, idempotent via `get_or_create` on POST. Audit
    is written to the todo's parent problem when one exists, falling back
    to `problem=None` for problemless todos — same patient-scope-legal-
    trail policy as the unpinned-observation case in PR-3.
    """
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'error': 'POST or DELETE required'}, status=405)

    if not _assert_patient_access(request.user, patient_id):
        return JsonResponse({'error': 'Patient not found'}, status=404)

    try:
        doc = Document.objects.get(id=document_id, patient_id=patient_id)
    except Document.DoesNotExist:
        return JsonResponse({'error': 'Document not found'}, status=404)

    try:
        todo = ToDo.objects.get(id=todo_id, patient_id=patient_id)
    except ToDo.DoesNotExist:
        return JsonResponse({'error': 'Todo not found'}, status=404)

    document_name = doc.document_name or 'document'
    # Todo audit lands on the todo's parent problem (if any), else null.
    audit_problem = todo.problem if todo.problem_id else None

    if request.method == 'DELETE':
        deleted, _ = DocumentTodo.objects.filter(
            document=doc, todo=todo,
        ).delete()
        if deleted:
            add_problem_activity(
                audit_problem, request.user,
                f"Unlinked document from todo: {document_name}"
            )
        return JsonResponse({'success': True})

    # POST -> get_or_create
    link, created = DocumentTodo.objects.get_or_create(
        document=doc, todo=todo,
        defaults={'author': request.user},
    )
    if created:
        add_problem_activity(
            audit_problem, request.user,
            f"Linked document to todo: {document_name}"
        )
    return JsonResponse({'success': True, 'id': link.id, 'created': created})


# ---------- Problem Image endpoints (PR-2, 2026-06-08) ----------

@csrf_exempt
@login_required
def mobile_upload_problem_image(request, patient_id, problem_id):
    """POST multipart -> upload a PatientImage attached to a Problem.

    Body (form-data):
      file         (required)  the JPEG binary (client must convert HEIC/PNG)
      client_uuid  (required)  iOS-side `ProblemImage.syncID` for idempotent
                               retry. get_or_create keyed on this; a retry
                               returns the same row id without re-saving
                               the file or emitting a duplicate audit row.
      file_name    (optional)  original filename for display
      caption      (optional)  freeform clinical context
      image_width  (optional)  pixels
      image_height (optional)  pixels

    PHI: gated by `_assert_patient_access`. GCS path is UUID-keyed via
    `set_problem_image_path` — no patient/problem IDs in the object key.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not _assert_patient_access(request.user, patient_id):
        return JsonResponse({'error': 'Patient not found'}, status=404)

    from django.contrib.auth.models import User
    try:
        patient_user = User.objects.get(id=patient_id)
        problem = Problem.objects.get(id=problem_id, patient_id=patient_id)
    except (User.DoesNotExist, Problem.DoesNotExist):
        return JsonResponse({'error': 'Patient or problem not found'}, status=404)

    image_file = request.FILES.get('file')
    if not image_file:
        return JsonResponse({'error': 'No image file provided'}, status=400)

    client_uuid = request.POST.get('client_uuid')
    if not client_uuid:
        # Required so retries can no-op rather than create duplicate rows.
        # Matches the encounter-audio upload contract from earlier work.
        return JsonResponse({'error': 'client_uuid is required'}, status=400)

    caption = request.POST.get('caption') or None
    file_name = request.POST.get('file_name') or image_file.name

    def _parse_int(key):
        try:
            val = int(request.POST.get(key, ''))
            return val if val > 0 else None
        except (TypeError, ValueError):
            return None

    image_width = _parse_int('image_width')
    image_height = _parse_int('image_height')

    img, created = PatientImage.objects.get_or_create(
        client_uuid=client_uuid,
        defaults={
            'patient': patient_user,
            'problem': problem,
            'image': image_file,
            'caption': caption,
            'file_name': file_name,
            'image_width': image_width,
            'image_height': image_height,
            'author': request.user,
        },
    )

    if created:
        add_problem_activity(
            problem, request.user,
            f"Added image: {file_name}"
        )

    return JsonResponse({'success': True, 'id': img.id, 'created': created})


@csrf_exempt
@login_required
def mobile_delete_problem_image(request, patient_id, image_id):
    """DELETE -> remove a PatientImage row + its GCS object.

    Idempotent: a retried DELETE after a lost response returns 200 success
    even if the row is already gone, so the iOS soft-delete queue clears
    cleanly. Matches the ProblemNote / ObservationValue DELETE contract
    from PR-1 / PR-3.
    """
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE required'}, status=405)

    if not _assert_patient_access(request.user, patient_id):
        return JsonResponse({'error': 'Image not found'}, status=404)

    try:
        img = PatientImage.objects.get(id=image_id, patient_id=patient_id)
    except PatientImage.DoesNotExist:
        # Genuinely gone — retry-safe success.
        return JsonResponse({'success': True})

    file_name = img.file_name or (
        os.path.basename(img.image.name) if img.image else 'image'
    )
    problem = img.problem

    if img.image:
        # Triggers the django-storages GCS backend delete, removing the
        # object. Set save=False since we follow with img.delete() right
        # after — no point persisting the cleared FileField.
        img.image.delete(save=False)
    img.delete()

    if problem is not None:
        add_problem_activity(
            problem, request.user,
            f"Removed image: {file_name}"
        )

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_save_my_story_entry(request, patient_id, component_id):
    """POST {text} -> create a new MyStoryTextComponentEntry."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth.models import User

    try:
        patient_user = User.objects.get(id=patient_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    try:
        component = MyStoryTextComponent.objects.get(id=component_id)
    except MyStoryTextComponent.DoesNotExist:
        return JsonResponse({'error': 'Component not found'}, status=404)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        body = request.POST

    text = body.get('text', '')
    if not text.strip():
        return JsonResponse({'error': 'Text is required'}, status=400)

    entry = MyStoryTextComponentEntry(
        component=component,
        text=text.strip(),
        patient=patient_user,
        author=request.user,
    )
    entry.save()

    return JsonResponse({'success': True, 'id': entry.id})


def _parse_body(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return request.POST


def _get_patient(patient_id):
    from django.contrib.auth.models import User
    return User.objects.get(id=patient_id)


def _assert_patient_access(user, patient_id):
    """Returns True if `user` has clinical access to `patient_id`'s data.

    PHI gate for the media proxy endpoints (audio, document, image) per the
    PR-2 RBAC requirement. Mirrors the role-by-role logic in `mobile_patients`
    (kept in lockstep — any change to one MUST flow to the other or the proxy
    will leak relative to the patient-list endpoint).

    Roles:
      admin                            -> any User row whose profile.role == 'patient'
      physician                        -> own PatientController patients
      secretary / mid-level / nurse    -> team physicians' PatientController patients
      patient                          -> themselves only
      other (no profile, no role, etc) -> deny

    Returns a plain bool. Callers translate False into a 404 (uniform with
    "not found", to avoid leaking the existence of an ID the user can't see).
    Currently used by `mobile_encounter_audio`, `mobile_document_file`,
    `mobile_image_file`, and the new `mobile_upload_problem_image` /
    `mobile_delete_problem_image` endpoints. Until PR-2 these proxy paths had
    NO patient-relationship verification — a classic IDOR. Do NOT remove the
    `_assert_patient_access` call from any of those endpoints.
    """
    try:
        patient_id = int(patient_id)
    except (TypeError, ValueError):
        return False

    try:
        role = user.profile.role
    except (UserProfile.DoesNotExist, AttributeError):
        return False

    if role == 'admin':
        return UserProfile.objects.filter(user_id=patient_id, role='patient').exists()
    elif role == 'physician':
        return PatientController.objects.filter(physician=user, patient_id=patient_id).exists()
    elif role in ('secretary', 'mid-level', 'nurse'):
        physician_ids = PhysicianTeam.objects.filter(member=user).values_list('physician_id', flat=True)
        return PatientController.objects.filter(physician_id__in=physician_ids, patient_id=patient_id).exists()
    elif role == 'patient':
        return user.id == patient_id
    return False


# ---------- Problem endpoints ----------

def _yesno_status(value, on_label, off_label):
    """Format a boolean as a human-readable status string for activity rows.
    Centralized so wording stays consistent across the mobile-API mutation
    endpoints; matches what the iOS app used to write locally pre-Bug-B."""
    return on_label if value else off_label


@csrf_exempt
@login_required
def mobile_create_problem(request, patient_id):
    """POST {problem_name, concept_id?, is_active?, is_controlled?} -> create Problem."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        patient_user = _get_patient(patient_id)
    except Exception:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    body = _parse_body(request)
    problem_name = body.get('problem_name', '').strip()
    if not problem_name:
        return JsonResponse({'error': 'problem_name is required'}, status=400)

    problem = Problem(
        patient=patient_user,
        problem_name=problem_name,
        concept_id=body.get('concept_id', '') or '',
        is_active=body.get('is_active', True),
        is_controlled=body.get('is_controlled', False),
    )
    problem.save()
    add_problem_activity(problem, request.user, f"Added problem: {problem_name}")
    return JsonResponse({'success': True, 'id': problem.id})


@csrf_exempt
@login_required
def mobile_update_problem(request, patient_id, problem_id):
    """PATCH {problem_name?, is_active?, is_controlled?, authenticated?, old_problem_name?}."""
    if request.method not in ('PATCH', 'POST'):
        return JsonResponse({'error': 'PATCH required'}, status=405)
    try:
        problem = Problem.objects.get(id=problem_id, patient_id=patient_id)
    except Problem.DoesNotExist:
        return JsonResponse({'error': 'Problem not found'}, status=404)

    body = _parse_body(request)

    # Snapshot pre-change values so we can emit accurate activity rows
    # comparing requested change against the prior state. Required because
    # `setattr` below overwrites the instance attributes before save.
    old_problem_name = problem.problem_name
    old_is_active = problem.is_active
    old_is_controlled = problem.is_controlled
    old_authenticated = problem.authenticated

    for field in ('problem_name', 'concept_id', 'old_problem_name'):
        if field in body:
            setattr(problem, field, body[field])
    for field in ('is_active', 'is_controlled', 'authenticated'):
        if field in body:
            setattr(problem, field, body[field])
    problem.save()

    # Activity rows — one per changed field. Mirrors what the iOS app used
    # to write locally before Bug B made the server authoritative.
    if 'problem_name' in body and problem.problem_name != old_problem_name:
        add_problem_activity(
            problem, request.user,
            f'Problem renamed from "{old_problem_name}" to "{problem.problem_name}"'
        )
    if 'is_active' in body and problem.is_active != old_is_active:
        add_problem_activity(
            problem, request.user,
            f"Changed status to {_yesno_status(problem.is_active, 'Active', 'Inactive')}"
        )
    if 'is_controlled' in body and problem.is_controlled != old_is_controlled:
        add_problem_activity(
            problem, request.user,
            f"Changed control status to {_yesno_status(problem.is_controlled, 'Controlled', 'Not Controlled')}"
        )
    if 'authenticated' in body and problem.authenticated != old_authenticated:
        add_problem_activity(
            problem, request.user,
            f"Changed authentication to {_yesno_status(problem.authenticated, 'Authenticated', 'Not Authenticated')}"
        )
    return JsonResponse({'success': True})


# ---------- Problem Note endpoints ----------

@csrf_exempt
@login_required
def mobile_create_problem_note(request, patient_id, problem_id):
    """POST {note, note_type} -> create ProblemNote."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        problem = Problem.objects.get(id=problem_id, patient_id=patient_id)
    except Problem.DoesNotExist:
        return JsonResponse({'error': 'Problem not found'}, status=404)

    body = _parse_body(request)
    note_text = body.get('note', '').strip()
    if not note_text:
        return JsonResponse({'error': 'note is required'}, status=400)

    note = ProblemNote(
        problem=problem,
        note=note_text,
        note_type=body.get('note_type', 'wiki'),
        author=request.user,
    )
    note.save()
    add_problem_activity(
        problem, request.user,
        f"Added {note.note_type} note: {note_text}"
    )
    return JsonResponse({'success': True, 'id': note.id})


@csrf_exempt
@login_required
def mobile_update_problem_note(request, patient_id, problem_id, note_id):
    """PATCH {note?, note_type?} -> update; DELETE -> remove ProblemNote.

    Activity audit row is emitted on every successful mutation (mirrors what
    the macOS app used to write locally pre-Bug-B). Excerpt truncated to 200
    chars to keep the ProblemActivity row from ballooning on paste-heavy notes.
    """
    if request.method not in ('PATCH', 'POST', 'DELETE'):
        return JsonResponse({'error': 'PATCH or DELETE required'}, status=405)

    try:
        note = ProblemNote.objects.get(
            id=note_id,
            problem_id=problem_id,
            problem__patient_id=patient_id,
        )
    except ProblemNote.DoesNotExist:
        # DELETE on an already-gone row is success — lets the client retry safely
        # if its first DELETE response was lost mid-network.
        if request.method == 'DELETE':
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Note not found'}, status=404)

    problem = note.problem

    if request.method == 'DELETE':
        old_text = note.note or ''
        old_type = note.note_type or 'wiki'
        note.delete()
        excerpt = old_text[:200]
        suffix = '...' if len(old_text) > 200 else ''
        add_problem_activity(
            problem, request.user,
            f"Deleted {old_type} note: {excerpt}{suffix}"
        )
        return JsonResponse({'success': True})

    # PATCH path
    body = _parse_body(request)
    has_note = 'note' in body
    has_type = 'note_type' in body
    if not has_note and not has_type:
        return JsonResponse({'error': 'At least one of note or note_type required'}, status=400)

    if has_note:
        new_text = (body.get('note') or '').strip()
        if not new_text:
            return JsonResponse({'error': 'note must be non-empty'}, status=400)
        note.note = new_text
    if has_type:
        # wiki↔history transitions are accepted; the audit row records the new type
        note.note_type = body.get('note_type') or 'wiki'
    note.save()

    excerpt = note.note[:200]
    suffix = '...' if len(note.note) > 200 else ''
    add_problem_activity(
        problem, request.user,
        f"Edited {note.note_type} note: {excerpt}{suffix}"
    )
    return JsonResponse({'success': True})


# ---------- Problem Label endpoints ----------

@csrf_exempt
@login_required
def mobile_create_problem_label(request, patient_id, problem_id):
    """POST {name, css_class?} -> create ProblemLabel and add to problem."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        patient_user = _get_patient(patient_id)
        problem = Problem.objects.get(id=problem_id, patient_id=patient_id)
    except Problem.DoesNotExist:
        return JsonResponse({'error': 'Problem not found'}, status=404)
    except Exception:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    body = _parse_body(request)
    name = body.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'name is required'}, status=400)

    label = ProblemLabel(
        name=name,
        css_class=body.get('css_class', ''),
        author=request.user,
        patient=patient_user,
    )
    label.save()
    problem.labels.add(label)
    return JsonResponse({'success': True, 'id': label.id})


# ---------- Problem Relationship endpoints ----------

@csrf_exempt
@login_required
def mobile_create_problem_relationship(request, patient_id):
    """POST {source_id, target_id} -> create ProblemRelationship."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    body = _parse_body(request)
    source_id = body.get('source_id')
    target_id = body.get('target_id')
    if not source_id or not target_id:
        return JsonResponse({'error': 'source_id and target_id are required'}, status=400)

    try:
        source = Problem.objects.get(id=source_id, patient_id=patient_id)
        target = Problem.objects.get(id=target_id, patient_id=patient_id)
    except Problem.DoesNotExist:
        return JsonResponse({'error': 'Problem not found'}, status=404)

    rel = ProblemRelationship(source=source, target=target)
    rel.save()
    return JsonResponse({'success': True, 'id': rel.id})


# ---------- Todo endpoints ----------

@csrf_exempt
@login_required
def mobile_create_todo(request, patient_id):
    """POST {todo, problem_id?, due_date?, order?} -> create ToDo."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        patient_user = _get_patient(patient_id)
    except Exception:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    body = _parse_body(request)
    todo_text = body.get('todo', '').strip()
    if not todo_text:
        return JsonResponse({'error': 'todo is required'}, status=400)

    from django.utils.dateparse import parse_datetime

    todo = ToDo(
        todo=todo_text,
        patient=patient_user,
        user=request.user,
    )
    problem_id = body.get('problem_id')
    if problem_id:
        try:
            todo.problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            pass
    due_date = body.get('due_date')
    if due_date:
        todo.due_date = parse_datetime(due_date)
    if 'order' in body:
        todo.order = body['order']
    todo.save()

    # Todo-side activity row + mirrored row on the linked problem if any.
    # Matches iOS pre-Bug-B behavior that wrote both rows locally.
    add_todo_activity(todo, request.user, f"Added todo: {todo_text}")
    if todo.problem is not None:
        add_problem_activity(
            todo.problem, request.user,
            f"Added todo: {todo_text}"
        )
    return JsonResponse({'success': True, 'id': todo.id})


@csrf_exempt
@login_required
def mobile_update_todo(request, patient_id, todo_id):
    """PATCH {todo?, accomplished?, due_date?, order?, problem_id?}."""
    if request.method not in ('PATCH', 'POST'):
        return JsonResponse({'error': 'PATCH required'}, status=405)
    try:
        todo = ToDo.objects.get(id=todo_id, patient_id=patient_id)
    except ToDo.DoesNotExist:
        return JsonResponse({'error': 'Todo not found'}, status=404)

    from django.utils.dateparse import parse_datetime

    body = _parse_body(request)

    # Snapshot fields that produce activity rows on change. Required so the
    # "renamed from X to Y" + accomplished-toggle rows reference the prior
    # state, not the post-save value.
    old_todo_title = todo.todo
    old_accomplished = todo.accomplished

    if 'todo' in body:
        todo.todo = body['todo']
    if 'accomplished' in body:
        todo.accomplished = body['accomplished']
    if 'due_date' in body:
        todo.due_date = parse_datetime(body['due_date']) if body['due_date'] else None
    if 'order' in body:
        todo.order = body['order']
    if 'problem_id' in body:
        if body['problem_id']:
            try:
                todo.problem = Problem.objects.get(id=body['problem_id'])
            except Problem.DoesNotExist:
                pass
        else:
            todo.problem = None
    todo.save()

    # Title change -> todo-side rename row. No problem-side mirror, matching
    # iOS pre-Bug-B asymmetry (only the toggle mirrored onto the problem).
    if 'todo' in body and todo.todo != old_todo_title:
        add_todo_activity(
            todo, request.user,
            f'Todo name changed from "{old_todo_title}" to "{todo.todo}"'
        )

    # Accomplished toggle -> todo-side row + mirrored row on the linked
    # problem. Matches iOS pre-Bug-B behavior.
    if 'accomplished' in body and todo.accomplished != old_accomplished:
        status_word = 'accomplished' if todo.accomplished else 'not accomplished'
        add_todo_activity(
            todo, request.user,
            f"Updated status to {status_word}"
        )
        if todo.problem is not None:
            add_problem_activity(
                todo.problem, request.user,
                f'Todo "{todo.todo}" marked {status_word}'
            )
    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_log_todo_print(request, patient_id, todo_id):
    """POST {provider_id?: int} -> emits a 'printed requisition' TodoActivity
    row. iOS fire-and-forgets this after a successful Order Requisition
    print so the audit trail mirrors the server-authoritative pattern
    documented in CLAUDE.md (vs. an iOS-local ActivityLogEntry write).
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    if not _assert_patient_access(request.user, patient_id):
        return JsonResponse({'error': 'Patient not found'}, status=404)

    try:
        todo = ToDo.objects.get(id=todo_id, patient_id=patient_id)
    except ToDo.DoesNotExist:
        return JsonResponse({'error': 'Todo not found'}, status=404)

    body = _parse_body(request)
    provider_id = body.get('provider_id')

    provider_name = ''
    if provider_id:
        from django.contrib.auth.models import User
        try:
            provider = User.objects.get(id=int(provider_id))
            provider_name = provider.get_full_name() or provider.username
        except (User.DoesNotExist, TypeError, ValueError):
            pass

    if provider_name:
        activity = f"Printed requisition signed by {provider_name}"
    else:
        activity = "Printed requisition"

    add_todo_activity(todo, request.user, activity)
    return JsonResponse({'success': True})


# ---------- Todo Comment endpoints ----------

@csrf_exempt
@login_required
def mobile_create_todo_comment(request, patient_id, todo_id):
    """POST {comment} -> create ToDoComment."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        todo = ToDo.objects.get(id=todo_id, patient_id=patient_id)
    except ToDo.DoesNotExist:
        return JsonResponse({'error': 'Todo not found'}, status=404)

    body = _parse_body(request)
    comment_text = body.get('comment', '').strip()
    if not comment_text:
        return JsonResponse({'error': 'comment is required'}, status=400)

    comment = ToDoComment(
        todo=todo,
        user=request.user,
        comment=comment_text,
    )
    comment.save()
    # Link the activity row to the comment FK so legacy web-app activity
    # feeds can render the comment body inline. iOS ignores the FK
    # (RemoteTodoActivity has no `comment` field) — harmless either way.
    add_todo_activity(todo, request.user, "Added comment", comment=comment)
    return JsonResponse({'success': True, 'id': comment.id})


# ---------- Todo Label endpoints ----------

@csrf_exempt
@login_required
def mobile_create_todo_label(request, patient_id, todo_id):
    """POST {name, css_class?} -> create Label and add to todo."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        todo = ToDo.objects.get(id=todo_id, patient_id=patient_id)
    except ToDo.DoesNotExist:
        return JsonResponse({'error': 'Todo not found'}, status=404)

    body = _parse_body(request)
    name = body.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'name is required'}, status=400)

    label = Label(
        name=name,
        css_class=body.get('css_class', ''),
        author=request.user,
    )
    label.save()
    todo.labels.add(label)
    return JsonResponse({'success': True, 'id': label.id})


# ---------- Todo Member endpoints ----------

@csrf_exempt
@login_required
def mobile_add_todo_member(request, patient_id, todo_id):
    """POST {user_id} -> tag a staff member on a todo."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        todo = ToDo.objects.get(id=todo_id, patient_id=patient_id)
    except ToDo.DoesNotExist:
        return JsonResponse({'error': 'Todo not found'}, status=404)

    body = _parse_body(request)
    user_id = body.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'user_id is required'}, status=400)

    from django.contrib.auth.models import User
    try:
        member = User.objects.get(id=int(user_id))
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    tto, created = TaggedToDoOrder.objects.get_or_create(todo=todo, user=member)
    # Only write the activity row on a fresh tag — get_or_create returning
    # an existing row means the member was already tagged, and emitting a
    # row in that case would be a phantom audit event.
    if created:
        member_name = member.get_full_name() or member.username
        try:
            role = member.profile.role
        except UserProfile.DoesNotExist:
            role = ''
        suffix = f" - {role}" if role else ""
        add_todo_activity(
            todo, request.user,
            f"{member_name}{suffix} joined this todo"
        )
    return JsonResponse({'success': True, 'id': tto.id})


@csrf_exempt
@login_required
def mobile_remove_todo_member(request, patient_id, todo_id, user_id):
    """DELETE -> untag a staff member from a todo."""
    if request.method != 'DELETE':
        return JsonResponse({'error': 'DELETE required'}, status=405)
    try:
        todo = ToDo.objects.get(id=todo_id, patient_id=patient_id)
    except ToDo.DoesNotExist:
        return JsonResponse({'error': 'Todo not found'}, status=404)

    # Fetch the row first so we can capture the member's display name for
    # the activity row. The previous bulk-filter-delete didn't load the
    # User, leaving us no way to write a meaningful audit string.
    try:
        tto = TaggedToDoOrder.objects.get(todo=todo, user_id=user_id)
    except TaggedToDoOrder.DoesNotExist:
        # Idempotent: same observable response as the old bulk-delete path
        # when the row doesn't exist — success, deleted=0, no activity row.
        return JsonResponse({'success': True, 'deleted': 0})

    member = tto.user
    member_name = member.get_full_name() or member.username
    tto.delete()
    add_todo_activity(todo, request.user, f"Unpinned {member_name}")
    return JsonResponse({'success': True, 'deleted': 1})


# ---------- Observation Value endpoints ----------

@csrf_exempt
@login_required
def mobile_create_observation_value(request, patient_id, component_id):
    """POST {value_quantity, effective_datetime?} -> create ObservationValue."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        component = ObservationComponent.objects.get(id=component_id)
    except ObservationComponent.DoesNotExist:
        return JsonResponse({'error': 'Component not found'}, status=404)

    from django.utils.dateparse import parse_datetime

    body = _parse_body(request)
    value_quantity = body.get('value_quantity')
    if value_quantity is None:
        return JsonResponse({'error': 'value_quantity is required'}, status=400)

    val = ObservationValue(
        component=component,
        value_quantity=value_quantity,
        author=request.user,
    )
    effective = body.get('effective_datetime')
    if effective:
        val.effective_datetime = parse_datetime(effective)
    val.save()
    return JsonResponse({'success': True, 'id': val.id})


def _emit_observation_audit(observation, user, activity):
    """Fan out a ProblemActivity row per pinned problem for the given
    observation. If the observation has no pins, write a single
    `problem=None` row to maintain the patient-scope legal trail.

    Per the PR-3 audit-routing decision (2026-06-08). Migration
    `0173_allow_null_problem_on_problem_activity` made the FK nullable
    specifically to support the unpinned case.
    """
    pins = list(ObservationPinToProblem.objects.filter(observation=observation))
    if pins:
        for pin in pins:
            add_problem_activity(pin.problem, user, activity)
    else:
        add_problem_activity(None, user, activity)


@csrf_exempt
@login_required
def mobile_update_observation(request, patient_id, observation_id):
    """PATCH {comments?} -> update parent Observation fields.

    Today this only carries the `comments` field — the macOS UI surfaces it
    as "Note" for clinical context (e.g. "Left arm, sitting"). Empty string
    or null clears the note. Fans out audit rows per pinned problem (or
    problem=None if unpinned).
    """
    if request.method not in ('PATCH', 'POST'):
        return JsonResponse({'error': 'PATCH required'}, status=405)

    try:
        observation = Observation.objects.get(id=observation_id, subject_id=patient_id)
    except Observation.DoesNotExist:
        return JsonResponse({'error': 'Observation not found'}, status=404)

    body = _parse_body(request)
    if 'comments' not in body:
        return JsonResponse({'error': 'comments field required'}, status=400)

    # Accept "" and null as the "clear" signal — both store as null in the DB
    # so a re-pull doesn't carry a phantom empty-string value back to the
    # client (which would defeat the preserveLocal guard on the iOS side).
    new_comments = body.get('comments')
    if new_comments == '':
        new_comments = None
    observation.comments = new_comments
    observation.save()

    if new_comments is None:
        msg = f"Cleared note on {observation.name or 'observation'}"
    else:
        excerpt = new_comments[:200]
        suffix = '...' if len(new_comments) > 200 else ''
        msg = f"Edited note on {observation.name or 'observation'}: {excerpt}{suffix}"
    _emit_observation_audit(observation, request.user, msg)

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_update_observation_value(request, patient_id, value_id):
    """PATCH {value_quantity?, value_unit?, effective_datetime?} -> update;
    DELETE -> hard-remove ObservationValue.

    Auth chain: value -> component -> observation, with the observation's
    subject_id matching patient_id. Audit fans out per pinned problem.
    """
    if request.method not in ('PATCH', 'POST', 'DELETE'):
        return JsonResponse({'error': 'PATCH or DELETE required'}, status=405)

    try:
        value = ObservationValue.objects.select_related(
            'component__observation'
        ).get(
            id=value_id,
            component__observation__subject_id=patient_id,
        )
    except ObservationValue.DoesNotExist:
        # DELETE on already-gone row is idempotent success — matches the
        # ProblemNote contract from PR-1.
        if request.method == 'DELETE':
            return JsonResponse({'success': True})
        return JsonResponse({'error': 'Value not found'}, status=404)

    observation = value.component.observation

    if request.method == 'DELETE':
        # Snapshot for audit before destroy.
        old_quantity = value.value_quantity
        old_unit = value.value_unit or ''
        value.delete()
        msg = f"Deleted {observation.name or 'observation'} reading: {old_quantity}{old_unit}"
        _emit_observation_audit(observation, request.user, msg)
        return JsonResponse({'success': True})

    # PATCH path
    from django.utils.dateparse import parse_datetime

    body = _parse_body(request)
    touched = False

    if 'value_quantity' in body:
        new_q = body.get('value_quantity')
        if new_q is None:
            return JsonResponse({'error': 'value_quantity cannot be null'}, status=400)
        value.value_quantity = new_q
        touched = True
    if 'value_unit' in body:
        value.value_unit = body.get('value_unit') or ''
        touched = True
    if 'effective_datetime' in body:
        effective = body.get('effective_datetime')
        if effective:
            value.effective_datetime = parse_datetime(effective)
            touched = True

    if not touched:
        return JsonResponse({'error': 'At least one field required'}, status=400)

    value.save()

    quantity_label = f"{value.value_quantity}{value.value_unit or ''}".strip()
    msg = f"Edited {observation.name or 'observation'} reading: {quantity_label}"
    _emit_observation_audit(observation, request.user, msg)

    return JsonResponse({'success': True})


@csrf_exempt
@login_required
def mobile_observation_pin(request, patient_id, observation_id, problem_id):
    """POST -> create (or no-op if already pinned) ObservationPinToProblem;
    DELETE -> remove the pin.

    URL-coordinate identity: a pin is fully described by
    (observation_id, problem_id), so POST is naturally idempotent — repeat
    calls return the same row id with success=True. Audit is written
    directly to the target problem (NOT via the helper) because the action
    is intrinsically a problem-level annotation, not a value mutation.
    """
    if request.method not in ('POST', 'DELETE'):
        return JsonResponse({'error': 'POST or DELETE required'}, status=405)

    try:
        observation = Observation.objects.get(id=observation_id, subject_id=patient_id)
    except Observation.DoesNotExist:
        return JsonResponse({'error': 'Observation not found'}, status=404)

    try:
        problem = Problem.objects.get(id=problem_id, patient_id=patient_id)
    except Problem.DoesNotExist:
        return JsonResponse({'error': 'Problem not found'}, status=404)

    if request.method == 'DELETE':
        # Idempotent delete: 200 success whether the row exists or not. The
        # macOS soft-delete queue depends on this so a retried DELETE after
        # a lost response doesn't strand the tombstone.
        deleted, _ = ObservationPinToProblem.objects.filter(
            observation=observation, problem=problem,
        ).delete()
        if deleted:
            add_problem_activity(
                problem, request.user,
                f"Unpinned {observation.name or 'observation'}"
            )
        return JsonResponse({'success': True})

    # POST path — get_or_create makes this idempotent. If the pin already
    # exists, no new ProblemActivity row is emitted (avoids audit noise from
    # client retries).
    pin, created = ObservationPinToProblem.objects.get_or_create(
        observation=observation,
        problem=problem,
        defaults={'author': request.user},
    )
    if created:
        add_problem_activity(
            problem, request.user,
            f"Pinned {observation.name or 'observation'} to this problem"
        )
    return JsonResponse({'success': True, 'id': pin.id, 'created': created})


# ---------- My Tagged Todos endpoint ----------

@csrf_exempt
@login_required
def mobile_my_tagged_todos(request):
    """GET -> all non-accomplished todos where the current user is tagged."""
    import sys
    import traceback as tb
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    last_todo_id = None
    try:
        tagged_orders = (
            TaggedToDoOrder.objects
            .filter(user=request.user, todo__accomplished=False, todo__isnull=False)
            .select_related('todo', 'todo__patient', 'todo__patient__profile', 'todo__problem')
            .prefetch_related('todo__labels', 'todo__comments', 'todo__comments__user')
        )

        todos = []
        for tto in tagged_orders:
            t = tto.todo
            last_todo_id = t.id if t else None
            members = []
            for m in TaggedToDoOrder.objects.filter(todo=t).select_related('user', 'user__profile'):
                member_role = ''
                if m.user:
                    try:
                        member_role = m.user.profile.role
                    except UserProfile.DoesNotExist:
                        member_role = ''
                members.append({
                    'id': m.id,
                    'user_id': m.user_id,
                    'username': m.user.username if m.user else '',
                    'user_name': m.user.get_full_name() if m.user else '',
                    'role': member_role,
                    'status': m.status,
                    'created_on': m.created_on.isoformat() if m.created_on else None,
                })
            patient_name = ''
            if t.patient:
                try:
                    patient_name = t.patient.get_full_name()
                except Exception:
                    patient_name = ''
            problem_name = None
            if t.problem:
                try:
                    problem_name = t.problem.problem_name
                except Exception:
                    problem_name = None
            todos.append({
                'id': t.id,
                'todo': t.todo or '',
                'accomplished': t.accomplished,
                'accomplished_at': t.accomplished_at.isoformat() if t.accomplished_at else None,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'problem_id': t.problem_id if t.problem_id else None,
                'problem_name': problem_name,
                'patient_id': t.patient_id,
                'patient_name': patient_name,
                'order': t.order,
                'created_on': t.created_on.isoformat() if t.created_on else None,
                'labels': [{'id': l.id, 'name': l.name or '', 'css_class': l.css_class or ''} for l in t.labels.all()],
                'comments': [{
                    'id': c.id,
                    'comment': c.comment or '',
                    'user_id': c.user_id,
                    'user_name': c.user.get_full_name() if c.user else '',
                    'datetime': c.datetime.isoformat() if c.datetime else None,
                } for c in t.comments.order_by('-datetime')],
                'members': members,
            })

        return JsonResponse({'success': True, 'todos': todos})
    except Exception as exc:
        trace = tb.format_exc()
        # Make sure the traceback hits stderr so Cloud Run captures it.
        print(f"mobile_my_tagged_todos failed (last todo id={last_todo_id}): {exc}\n{trace}", file=sys.stderr, flush=True)
        return JsonResponse({
            'success': False,
            'error': str(exc),
            'last_todo_id': last_todo_id,
            'trace': trace,
        }, status=500)


# ---------- Label Catalog endpoints ----------

@csrf_exempt
@login_required
def mobile_create_label(request):
    """POST {name, css_class?, is_all?} -> create a catalog Label."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    body = _parse_body(request)
    name = body.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'name is required'}, status=400)

    label = Label(
        name=name,
        css_class=body.get('css_class', ''),
        author=request.user,
        is_all=bool(body.get('is_all', False)),
    )
    label.save()
    return JsonResponse({
        'success': True,
        'id': label.id,
        'name': label.name,
        'css_class': label.css_class,
        'is_all': label.is_all,
        'author_id': label.author_id,
    })


@csrf_exempt
@login_required
def mobile_update_label(request, label_id):
    """PATCH {name?, css_class?, is_all?} -> update a catalog Label."""
    if request.method not in ('PATCH', 'POST'):
        return JsonResponse({'error': 'PATCH or POST required'}, status=405)

    try:
        label = Label.objects.get(id=label_id)
    except Label.DoesNotExist:
        return JsonResponse({'error': 'Label not found'}, status=404)

    if not label.is_all and label.author_id != request.user.id:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    body = _parse_body(request)
    if 'name' in body:
        label.name = body['name'].strip()
    if 'css_class' in body:
        label.css_class = body['css_class']
    if 'is_all' in body:
        label.is_all = bool(body['is_all'])
    label.save()
    return JsonResponse({
        'success': True,
        'id': label.id,
        'name': label.name,
        'css_class': label.css_class,
        'is_all': label.is_all,
        'author_id': label.author_id,
    })


# ---------------------------------------------------------------------------
# Analytics: batch event ingestion
# ---------------------------------------------------------------------------

@csrf_exempt
@login_required
def mobile_batch_events(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from apps.analytics_app.models import UserEvent
    from dateutil.parser import isoparse

    body = json.loads(request.body)
    events_data = body.get('events', [])

    if not events_data:
        return JsonResponse({'success': True, 'count': 0})

    objects = []
    for e in events_data:
        meta = e.get('metadata')
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except (json.JSONDecodeError, TypeError):
                pass

        objects.append(UserEvent(
            timestamp=isoparse(e['timestamp']),
            user=request.user,
            action=e['action'],
            entity_type=e.get('entity_type'),
            entity_id=e.get('entity_id'),
            metadata=meta,
            patient_session_id=e['patient_session_id'],
            sequence=e['sequence'],
            event_schema_version=e.get('event_schema_version', 1),
            app_version=e.get('app_version', 'unknown'),
        ))

    UserEvent.objects.bulk_create(objects)

    return JsonResponse({'success': True, 'count': len(objects)})


# ---------------------------------------------------------------------------
# Error reporting: batch ingestion → Cloud Logging → Cloud Error Reporting
# ---------------------------------------------------------------------------

# PHI scrub policy: the iOS client buffers caught errors locally and ships
# them here. We are the single redaction point before structured logs hit
# Cloud Logging. Stack traces, app/OS versions, and the hardware model are
# preserved verbatim — symbolication and grouping in Cloud Error Reporting
# need those intact. The `message` field and any URL paths inside it are
# scrubbed: numeric path components on /api/patient/<id>/... become
# <redacted>, and any standalone 5+ digit number is dropped (the iOS user
# id is 1-4 digits, and 5+ digit numbers are almost always patient/record
# remoteIDs). `recordPersistentID` is SHA-256 hashed because it's an
# opaque SwiftData identifier with no analytical value but could
# theoretically correlate back to a row in someone's local DB.

_ERROR_LOGGER = logging.getLogger('smallbrain.error_reporter')

_PATIENT_PATH_RE = re.compile(r'(/api/patient/)\d+')
_LONG_NUMERIC_RE = re.compile(r'\b\d{5,}\b')


def _scrub_phi_message(message):
    if not message:
        return message
    scrubbed = _PATIENT_PATH_RE.sub(r'\1<redacted>', message)
    scrubbed = _LONG_NUMERIC_RE.sub('<redacted>', scrubbed)
    return scrubbed


def _hash_persistent_id(pid):
    if not pid:
        return None
    return hashlib.sha256(pid.encode('utf-8')).hexdigest()[:16]


@csrf_exempt
@login_required
def mobile_batch_errors(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'invalid JSON'}, status=400)

    errors_data = body.get('errors', [])
    if not errors_data:
        return JsonResponse({'success': True, 'received': 0})

    for e in errors_data:
        app_version = e.get('app_version', 'unknown')
        payload = {
            'severity': 'ERROR',
            'message': _scrub_phi_message(e.get('message', '')),
            'errorType': e.get('error_type', 'unknown'),
            'recordType': e.get('record_type'),
            'recordPersistentIDHash': _hash_persistent_id(e.get('record_persistent_id')),
            'timestamp': e.get('timestamp'),
            'userId': e.get('user_id'),
            'appVersion': app_version,
            'osVersion': e.get('os_version'),
            'deviceModel': e.get('device_model'),
            'errorSchemaVersion': e.get('error_schema_version', 1),
            # serviceContext drives Cloud Error Reporting grouping. The
            # stackTrace is preserved verbatim — CER pattern-matches the
            # message field for stack frames, so we surface any trace text
            # into `message` (already scrubbed above) and keep the raw
            # `stackTrace` alongside for engineer review.
            'serviceContext': {
                'service': 'smallbrain-macos',
                'version': app_version,
            },
            'stackTrace': e.get('stack_trace'),
        }
        _ERROR_LOGGER.error(json.dumps(payload))

    return JsonResponse({'success': True, 'received': len(errors_data)})


# ---------------------------------------------------------------------------
# Terminology mapping
# ---------------------------------------------------------------------------

_ADVICE_NOISE = {
    'DESCENDANTS NOT EXHAUSTIVELY MAPPED',
    'MAP OF SOURCE CONCEPT IS CONTEXT DEPENDENT',
    'CONSIDER ADDITIONAL CODE TO IDENTIFY SPECIFIC CONDITION OR DISEASE',
    'POSSIBLE REQUIREMENT FOR AN EXTERNAL CAUSE CODE',
    'POSSIBLE REQUIREMENT FOR PLACE OF OCCURRENCE',
}


def _humanize_map_advice(advice):
    """Convert raw NLM map_advice strings into a short, clinician-friendly hint.
    Returns None when there's nothing useful to surface (e.g. plain 'ALWAYS X' defaults)."""
    if not advice:
        return None

    import re
    upper = advice.upper()

    # Age-based conditional rules
    m = re.search(r'AGE AT ONSET[^|]*BEFORE\s+(\d+(?:\.\d+)?)\s+DAYS', upper)
    if m:
        days = int(float(m.group(1)))
        return f'Neonatal (< {days} days)' if days <= 29 else f'Onset before {days} days'
    m = re.search(r'AGE AT ONSET[^|]*BEFORE\s+(\d+(?:\.\d+)?)\s+YEARS', upper)
    if m:
        return f'Onset before {int(float(m.group(1)))} years'
    m = re.search(r'AGE AT ONSET[^|]*OVER\s+(\d+(?:\.\d+)?)\s+YEARS', upper)
    if m:
        return f'Onset after {int(float(m.group(1)))} years'

    # Sex-based conditional rules
    if 'FEMALE' in upper and 'MALE' not in re.sub(r'FEMALE', '', upper):
        return 'Female only'
    if re.search(r'\bMALE\b', upper) and 'FEMALE' not in upper:
        return 'Male only'

    # Trimester / pregnancy rules
    if 'TRIMESTER' in upper:
        if 'FIRST' in upper:
            return 'First trimester'
        if 'SECOND' in upper:
            return 'Second trimester'
        if 'THIRD' in upper:
            return 'Third trimester'

    # Plain "ALWAYS X" defaults → drop standard noise modifiers
    if upper.startswith('ALWAYS'):
        return None

    return None


@login_required
def get_snomed_to_icd10(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    concept_id = request.GET.get('concept_id', '').strip()
    if not concept_id:
        return JsonResponse({'error': 'concept_id query parameter is required'}, status=400)

    from emr.models import SnomedIcd10Map

    rows = SnomedIcd10Map.objects.filter(
        snomed_concept_id=concept_id
    ).exclude(
        map_advice__icontains='NON-BILLABLE'
    ).exclude(
        map_advice__icontains='ADDITIONAL DIGITS REQUIRED'
    ).order_by('map_group', 'map_priority')

    # Dedupe by icd10_code: keep the first (lowest map_group/map_priority) per unique target.
    seen = set()
    result = []
    for row in rows:
        if row.icd10_code in seen:
            continue
        seen.add(row.icd10_code)
        result.append({
            'code': row.icd10_code,
            'name': row.icd10_code,
            'advice': _humanize_map_advice(row.map_advice),
        })

    return JsonResponse(result, safe=False)
