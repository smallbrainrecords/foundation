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
    }


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
    patients = User.objects.filter(id__in=patient_user_ids).select_related('profile')

    result = []
    for u in patients:
        d = _user_dict(u)
        d['problem_count'] = Problem.objects.filter(patient=u, is_active=True).count()
        d['todo_count'] = ToDo.objects.filter(patient=u, accomplished=False).count()
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
                values_qs = ObservationValue.objects.filter(component=comp).order_by('-effective_datetime')
                if since:
                    values_qs = values_qs.filter(effective_datetime__gte=since)
                else:
                    values_qs = values_qs[:max_obs_values]
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
                'physician_id': enc.physician_id,
                'physician_name': physician_name,
                'start_time': enc.starttime.isoformat(),
                'stop_time': enc.stoptime.isoformat() if enc.stoptime else None,
                'audio_path': str(enc.audio) if enc.audio else '',
                'note': enc.note or '',
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
    """GET -> stream the audio file for an encounter."""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    try:
        enc = Encounter.objects.get(id=encounter_id)
    except Encounter.DoesNotExist:
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
    """GET -> stream the file for a document."""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET required'}, status=405)

    try:
        doc = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
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
def mobile_upload_encounter_audio(request, patient_id):
    """POST multipart: create encounter record + upload audio file."""
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

    note = request.POST.get('note', '')
    recorder_status = int(request.POST.get('recorder_status', 2))

    enc = Encounter(
        physician=request.user,
        patient=patient_user,
        audio=audio_file,
        note=note,
        recorder_status=recorder_status,
    )
    stop_time = request.POST.get('stop_time')
    if stop_time:
        enc.stoptime = parse_datetime(stop_time)
    enc.save()

    start_time = request.POST.get('start_time')
    if start_time:
        parsed = parse_datetime(start_time)
        if parsed:
            Encounter.objects.filter(id=enc.id).update(starttime=parsed)

    return JsonResponse({'success': True, 'id': enc.id})


@csrf_exempt
@login_required
def mobile_upload_document(request, patient_id):
    """POST multipart: create document record + upload file."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    from django.contrib.auth.models import User

    try:
        patient_user = User.objects.get(id=patient_id)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    doc_file = request.FILES.get('file')
    if not doc_file:
        return JsonResponse({'error': 'No file provided'}, status=400)

    document_name = request.POST.get('document_name', doc_file.name)

    doc = Document(
        document=doc_file,
        document_name=document_name,
        author=request.user,
        patient=patient_user,
    )
    doc.save()

    return JsonResponse({'success': True, 'id': doc.id})


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


# ---------- Problem endpoints ----------

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
    for field in ('problem_name', 'concept_id', 'old_problem_name'):
        if field in body:
            setattr(problem, field, body[field])
    for field in ('is_active', 'is_controlled', 'authenticated'):
        if field in body:
            setattr(problem, field, body[field])
    problem.save()
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
    return JsonResponse({'success': True, 'id': note.id})


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

    deleted, _ = TaggedToDoOrder.objects.filter(todo=todo, user_id=user_id).delete()
    return JsonResponse({'success': True, 'deleted': deleted})


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
