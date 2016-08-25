from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *

from emr.models import Observation, AOneCTextNote, ObservationComponent, UserProfile, ObservationComponentTextNote, \
    AOneC
from .serializers import AOneCTextNoteSerializer, AOneCSerializer
from data_app.serializers import ObservationComponentTextNoteSerializer, ObservationComponentSerializer, ObservationSerializer
from emr.operations import op_add_event

from problems_app.operations import add_problem_activity


# set problem authentication to false if not physician, admin
def set_problem_authentication_false(actor_profile, problem):
    role = actor_profile.role
    authenticated = role in ["physician", "admin"]
    problem.authenticated = authenticated
    problem.save()

@login_required
def track_a1c_click(request, a1c_id):
    actor = request.user
    a1c_info = AOneC.objects.get(id=a1c_id)
    patient = a1c_info.problem.patient

    summary = "<b>%s</b> visited <u>a1c</u> module" % (actor.username)
    op_add_event(actor, patient, summary, a1c_info.problem)

    resp = {}
    return ajax_response(resp)

@login_required
def get_a1c_info(request, a1c_id):
    a1c_info = AOneC.objects.get(id=a1c_id)
    resp = {}
    resp['success'] = True
    resp['info'] = AOneCSerializer(a1c_info).data
    return ajax_response(resp)


# Note
@permissions_required(["add_a1c_note"])
@login_required
def add_note(request, a1c_id):
    note = request.POST.get("note")
    a1c_note = AOneCTextNote.objects.create(a1c_id=a1c_id,
                                            author=request.user.profile, note=note)
    resp = {}
    resp['note'] = AOneCTextNoteSerializer(a1c_note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["edit_a1c_note"])
@login_required
def edit_note(request, note_id):
    note = AOneCTextNote.objects.get(id=note_id)
    note.note = request.POST.get('note')
    note.save()

    resp = {}
    resp['note'] = AOneCTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_a1c_note"])
@login_required
def delete_note(request, note_id):
    AOneCTextNote.objects.get(id=note_id).delete()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_a1c"])
@login_required
def patient_refused(request, a1c_id):
    a1c = AOneC.objects.get(id=a1c_id)
    observation = a1c.observation
    observation.effective_datetime = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
    observation.save()
    if request.POST.get('patient_refused_A1C', None):
        a1c.patient_refused_A1C = True

    a1c.save()
    # set problem authentication
    actor_profile = UserProfile.objects.get(user=actor)
    set_problem_authentication_false(actor_profile, a1c.problem)

    summary = """
        Patient refused a1c ,
        <u>problem</u> <b>%s</b>
        """ % (a1c.problem.problem_name)

    add_problem_activity(a1c.problem, actor_profile, summary)

    resp = {}
    resp['a1c'] = AOneCSerializer(a1c).data
    resp['success'] = True
    return ajax_response(resp)


# Value
@permissions_required(["add_a1c"])
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

    a1c = observation.observation_aonecs
    a1c.patient_refused_A1C = False
    a1c.todo_past_six_months = False
    a1c.save()

    resp['component'] = ObservationComponentSerializer(component).data
    resp['success'] = True

    # set problem authentication
    set_problem_authentication_false(actor_profile, a1c.problem)

    summary = """
        Added new a1c value <u>A1C</u> : <b>%s</b> ,
        <u>problem</u> <b>%s</b>
        """ % (component.value_quantity, a1c.problem.problem_name)

    add_problem_activity(a1c.problem, actor_profile, summary)

    summary = "An A1C value of <b>%s</b> was entered" % (component.value_quantity)
    op_add_event(request.user, a1c.problem.patient, summary, a1c.problem)
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
    resp['a1c_id'] = observation_component_info.observation.observation_aonecs.id
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
@permissions_required(["add_a1c_note"])
@login_required
def add_component_note(request, component_id):
    note = ObservationComponentTextNote.objects.create(observation_component_id=component_id,
                                                      author=request.user.profile,
                                                      note=request.POST.get("note"))
    resp = {}
    resp['note'] = ObservationComponentTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["edit_a1c_note"])
@login_required
def edit_component_note(request, note_id):
    note = ObservationComponentTextNote.objects.get(id=note_id)
    note.note = request.POST.get('note')
    note.save()

    resp = {}
    resp['note'] = ObservationComponentTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_a1c_note"])
@login_required
def delete_component_note(request, note_id):
    ObservationComponentTextNote.objects.get(id=note_id).delete()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)
