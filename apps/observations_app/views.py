from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *

from emr.models import Observation, ObservationTextNote, ObservationComponent, UserProfile, ObservationComponentTextNote
from .serializers import ObservationSerializer, ObservationTextNoteSerializer, ObservationComponentSerializer, ObservationComponentTextNoteSerializer

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity


# set problem authentication to false if not physician, admin
def set_problem_authentication_false(request, problem):
        
    actor_profile = UserProfile.objects.get(user=request.user)

    role = actor_profile.role

    if role in ['physician', 'admin']:
        authenticated = True
    else:
        authenticated = False

    problem.authenticated = authenticated
    problem.save()

@login_required
def get_observation_info(request, observation_id):
    observation_info = Observation.objects.get(id=observation_id)
    observation_dict = ObservationSerializer(observation_info).data

    resp = {}
    resp['success'] = True
    resp['info'] = observation_dict

    return ajax_response(resp)


# Note
@login_required
def add_note(request, observation_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_observation_note']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        note = ObservationTextNote()
        note.observation = Observation.objects.get(id=observation_id)
        note.author = request.user.profile
        note.note = request.POST.get('note')
        note.save()

        new_note_dict = ObservationTextNoteSerializer(note).data
        resp['note'] = new_note_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def edit_note(request, note_id):

    resp = {}
    resp['success'] = False

    permissions = ['edit_observation_note']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        note = ObservationTextNote.objects.get(id=note_id)
        note.note = request.POST.get('note')
        note.save()

        new_note_dict = ObservationTextNoteSerializer(note).data
        resp['note'] = new_note_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_note(request, note_id):

    resp = {}
    resp['success'] = False

    permissions = ['delete_observation_note']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        note = ObservationTextNote.objects.get(id=note_id)
        note.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def patient_refused(request, observation_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_observation']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        observation = Observation.objects.get(id=observation_id)
        observation.effective_datetime = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
        if request.POST.get('patient_refused_A1C', None):
            observation.patient_refused_A1C = True

        observation.save()

        new_observation_dict = ObservationSerializer(observation).data
        resp['observation'] = new_observation_dict
        resp['success'] = True

        # set problem authentication
        set_problem_authentication_false(request, observation.problem)

        summary = """
            Patient refused a1c ,
            <u>problem</u> <b>%s</b>
            """ % (observation.problem.problem_name)

        add_problem_activity(observation.problem, actor_profile, summary)

    return ajax_response(resp)


# Value
@login_required
def add_value(request, observation_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_observation']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        observation = Observation.objects.get(id=observation_id)
        component = ObservationComponent()
        component.observation = observation
        component.value_quantity = request.POST.get('value', None)
        component.effective_datetime = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
        component.author = actor_profile

        component.save()

        observation.patient_refused_A1C = False
        observation.todo_past_six_months = False
        observation.save()

        new_component_dict = ObservationComponentSerializer(component).data
        resp['component'] = new_component_dict
        resp['success'] = True

        # set problem authentication
        set_problem_authentication_false(request, component.observation.problem)

        summary = """
            Added new a1c value <u>A1C</u> : <b>%s</b> ,
            <u>problem</u> <b>%s</b>
            """ % (component.value_quantity, component.observation.problem.problem_name)

        add_problem_activity(component.observation.problem, actor_profile, summary)

    return ajax_response(resp)

@login_required
def delete_component(request, component_id):

    resp = {}
    resp['success'] = False

    permissions = ['delete_observation_component']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        component = ObservationComponent.objects.get(id=component_id)
        component.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_observation_component_info(request, component_id):
    observation_component_info = ObservationComponent.objects.get(id=component_id)
    observation_component_dict = ObservationComponentSerializer(observation_component_info).data

    resp = {}
    resp['success'] = True
    resp['info'] = observation_component_dict
    resp['observation_id'] = observation_component_info.observation.id

    return ajax_response(resp)

@login_required
def edit_component(request, component_id):

    resp = {}
    resp['success'] = False

    permissions = ['edit_observation_component']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        component = ObservationComponent.objects.get(id=component_id)
        component.value_quantity = request.POST.get('value_quantity')
        component.effective_datetime = datetime.strptime(request.POST.get('effective_datetime'), '%Y-%m-%d').date()
        component.save()

        observation_component_dict = ObservationComponentSerializer(component).data

        resp['success'] = True
        resp['info'] = observation_component_dict

    return ajax_response(resp)

# Component Note
@login_required
def add_component_note(request, component_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_observation_note']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        note = ObservationComponentTextNote()
        note.observation_component = ObservationComponent.objects.get(id=component_id)
        note.author = request.user.profile
        note.note = request.POST.get('note')
        note.save()

        new_note_dict = ObservationComponentTextNoteSerializer(note).data
        resp['note'] = new_note_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def edit_component_note(request, note_id):

    resp = {}
    resp['success'] = False

    permissions = ['edit_observation_note']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        note = ObservationComponentTextNote.objects.get(id=note_id)
        note.note = request.POST.get('note')
        note.save()

        new_note_dict = ObservationComponentTextNoteSerializer(note).data
        resp['note'] = new_note_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_component_note(request, note_id):

    resp = {}
    resp['success'] = False

    permissions = ['delete_observation_note']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        note = ObservationComponentTextNote.objects.get(id=note_id)
        note.delete()

        resp['success'] = True

    return ajax_response(resp)