from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *

from emr.models import Observation, ObservationTextNote, ObservationComponent, UserProfile, ObservationComponentTextNote
from .serializers import ObservationSerializer, ObservationTextNoteSerializer, ObservationComponentSerializer, ObservationComponentTextNoteSerializer
from emr.operations import op_add_event

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity
from problems_app.views import permissions_required


# set problem authentication to false if not physician, admin
def set_problem_authentication_false(actor_profile, problem):
    role = actor_profile.role
    authenticated = role in ["physician", "admin"]
    problem.authenticated = authenticated
    problem.save()

@login_required
def track_observation_click(request, observation_id):
    actor = request.user
    observation_info = Observation.objects.get(id=observation_id)
    patient = observation_info.problem.patient

    summary = "<b>%s</b> visited <u>a1c</u> module" % (actor.username)
    op_add_event(actor, patient, summary, observation_info.problem)

    resp = {}
    return ajax_response(resp)

@login_required
def get_observation_info(request, observation_id):
    observation_info = Observation.objects.get(id=observation_id)
    resp = {}
    resp['success'] = True
    resp['info'] = ObservationSerializer(observation_info).data
    return ajax_response(resp)


# Note
@permissions_required(["add_observation_note"])
@login_required
def add_note(request, observation_id):
    note = request.POST.get("note")
    observation_note = ObservationTextNote.objects.create(observation_id=observation_id,
                                                          author=request.user.profile, note=note)
    resp = {}
    resp['note'] = ObservationTextNoteSerializer(observation_note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["edit_observation_note"])
@login_required
def edit_note(request, note_id):
    note = ObservationTextNote.objects.get(id=note_id)
    note.note = request.POST.get('note')
    note.save()

    resp = {}
    resp['note'] = ObservationTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_observation_note"])
@login_required
def delete_note(request, note_id):
    ObservationTextNote.objects.get(id=note_id).delete()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_observation"])
@login_required
def patient_refused(request, observation_id):
    observation = Observation.objects.get(id=observation_id)
    observation.effective_datetime = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
    if request.POST.get('patient_refused_A1C', None):
        observation.patient_refused_A1C = True

    observation.save()
    # set problem authentication
    actor_profile = UserProfile.objects.get(user=actor)
    set_problem_authentication_false(actor_profile, observation.problem)

    summary = """
        Patient refused a1c ,
        <u>problem</u> <b>%s</b>
        """ % (observation.problem.problem_name)

    add_problem_activity(observation.problem, actor_profile, summary)

    resp = {}
    resp['observation'] = ObservationSerializer(observation).data
    resp['success'] = True
    return ajax_response(resp)


# Value
@permissions_required(["add_observation"])
@login_required
def add_value(request, observation_id):
    resp = {}
    actor_profile = UserProfile.objects.get(user=request.user)
    observation = Observation.objects.get(id=observation_id)
    effective_date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()

    component = ObservationComponent.objects.create(observation=observation,
                                                   value_quantity=request.POST.get("value", None),
                                                   effective_datetime=effective_date,
                                                   author=actor_profile)
    observation.patient_refused_A1C = False
    observation.todo_past_six_months = False
    observation.save()

    resp['component'] = ObservationComponentSerializer(component).data
    resp['success'] = True

    # set problem authentication
    set_problem_authentication_false(actor_profile, component.observation.problem)

    summary = """
        Added new a1c value <u>A1C</u> : <b>%s</b> ,
        <u>problem</u> <b>%s</b>
        """ % (component.value_quantity, component.observation.problem.problem_name)

    add_problem_activity(component.observation.problem, actor_profile, summary)

    summary = "An A1C value of <b>%s</b> was entered" % (component.value_quantity)
    op_add_event(request.user, observation.problem.patient, summary, observation.problem)
    return ajax_response(resp)


@permissions_required(["delete_observation_component"])
@login_required
def delete_component(request, component_id):
    ObservationComponent.objects.get(id=component_id).delete()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_observation_component_info(request, component_id):
    observation_component_info = ObservationComponent.objects.get(id=component_id)
    resp = {}
    resp['success'] = True
    resp['info'] = ObservationComponentSerializer(observation_component_info).data
    resp['observation_id'] = observation_component_info.observation.id
    return ajax_response(resp)


@permissions_required(["edit_observation_component"])
@login_required
def edit_component(request, component_id):
    component = ObservationComponent.objects.get(id=component_id)
    component.value_quantity = request.POST.get('value_quantity')
    component.effective_datetime = datetime.strptime(request.POST.get('effective_datetime'), '%Y-%m-%d').date()
    component.save()

    resp = {}
    resp['success'] = True
    resp['info'] = ObservationComponentSerializer(component).data
    return ajax_response(resp)


# Component Note
@permissions_required(["add_observation_note"])
@login_required
def add_component_note(request, component_id):
    note = ObservationComponentTextNote.objects.create(observation_component_id=component_id,
                                                      author=request.user.profile,
                                                      note=request.POST.get("note"))
    resp = {}
    resp['note'] = ObservationComponentTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["edit_observation_note"])
@login_required
def edit_component_note(request, note_id):
    note = ObservationComponentTextNote.objects.get(id=note_id)
    note.note = request.POST.get('note')
    note.save()

    resp = {}
    resp['note'] = ObservationComponentTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_observation_note"])
@login_required
def delete_component_note(request, note_id):
    ObservationComponentTextNote.objects.get(id=note_id).delete()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)
