from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *

from emr.models import Observation, ObservationTextNote, ObservationComponent, UserProfile
from .serializers import ObservationSerializer, ObservationTextNoteSerializer, ObservationComponentSerializer

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity


# set problem authentication to false if not physician, admin
def set_problem_authentication_false(request, component):
    if component.observation.problem:
        problem = component.observation.problem
        
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
        component.value_quantity = request.POST.get('value')
        component.effective_datetime = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
        if request.POST.get('patient_refused_A1C', None):
            component.patient_refused_A1C = True

        component.save()

        observation.todo_past_six_months = False
        observation.save()

        new_component_dict = ObservationComponentSerializer(component).data
        resp['component'] = new_component_dict
        resp['success'] = True

        # set problem authentication
        set_problem_authentication_false(request, component)

        summary = """
            Added new a1c value <u>A1C</u> : <b>%s</b> ,
            <u>problem</u> <b>%s</b>
            """ % (component.value_quantity, component.observation.problem.problem_name)

        add_problem_activity(component.observation.problem, actor_profile, summary)

    return ajax_response(resp)