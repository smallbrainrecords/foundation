from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import Observation, ObservationComponent, ObservationComponentTextNote, ObservationOrder, \
    PhysicianTeam, PatientController, ObservationPinToProblem, Problem
from emr.models import OBSERVATION_TYPES
from .serializers import ObservationComponentTextNoteSerializer, ObservationComponentSerializer, \
    ObservationSerializer, ObservationPinToProblemSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
from users_app.views import permissions_accessed


@login_required
def track_observation_click(request, observation_id):
    resp = {}
    resp['success'] = False
    observation = Observation.objects.get(id=observation_id)
    if permissions_accessed(request.user, observation.subject.user.id):
        actor = request.user
        patient = observation.subject.user

        summary = "<b>%s</b> accessed %s" % (actor.username, observation.name)
        op_add_event(actor, patient, summary)
        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_datas(request, patient_id):
    resp = {}
    resp['success'] = False
    
    if permissions_accessed(request.user, int(patient_id)):
        observations = Observation.objects.filter(subject__user__id=int(patient_id)).exclude(name=OBSERVATION_TYPES['a1c']['name']).filter(observation_aonecs=None)
        
        if request.user.profile.role == 'nurse' or request.user.profile.role == 'secretary':
            team_members = PhysicianTeam.objects.filter(member=request.user)
            if team_members:
                user = team_members[0].physician
            else:
                user = request.user
        else:
            user = request.user
        try:
            observation_order = ObservationOrder.objects.get(user=user, patient_id=patient_id)
        except ObservationOrder.DoesNotExist:
            observation_order = ObservationOrder(user=user, patient_id=patient_id)
            observation_order.save()

        observation_list = []
        for key in observation_order.order:
            if observations.filter(id=key):
                observation = observations.get(id=key)
                observation_dict = ObservationSerializer(observation).data
                observation_list.append(observation_dict)

        for observation in observations:
            if not observation.id in observation_order.order:
                observation_dict = ObservationSerializer(observation).data
                observation_list.append(observation_dict)


        resp['success'] = True
        resp['info'] = observation_list
    return ajax_response(resp)


@login_required
def get_observation_info(request, observation_id):
    observation = Observation.objects.get(id=observation_id)
    resp = {}
    resp['success'] = True
    resp['info'] = ObservationSerializer(observation).data
    return ajax_response(resp)

@login_required
@api_view(["POST"])
def add_new_data_type(request, patient_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        observation = Observation.objects.create(subject_id=int(patient_id),
                                       author=request.user.profile,
                                       name=request.POST.get("name", None),
                                       code=request.POST.get("code", None),
                                       color=request.POST.get("color", None))

        observation.save()

        resp['observation'] = ObservationSerializer(observation).data
        resp['success'] = True

    return ajax_response(resp)

@permissions_required(["set_data_order"])
@login_required
def update_order(request):
    resp = {}
    resp['success'] = False

    datas = json.loads(request.body)
    if datas.has_key('patient_id'):
        id_datas = datas['datas']
        patient_id = datas['patient_id']
        try:
            order = ObservationOrder.objects.get(user=request.user, patient_id=patient_id)
        except ObservationOrder.DoesNotExist:
            order = ObservationOrder(user=request.user, patient_id=patient_id)
            order.save()

        order.order = id_datas
        order.save()


        resp['success'] = True
    return ajax_response(resp)

@login_required
def get_pins(request, observation_id):
    pins = ObservationPinToProblem.objects.filter(observation_id=observation_id)
    resp = {}
    resp['success'] = True
    resp['pins'] = ObservationPinToProblemSerializer(pins, many=True).data
    return ajax_response(resp)

@login_required
@api_view(["POST"])
def obseration_pin_to_problem(request, patient_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        observation_id = request.POST.get("data_id", None)
        problem_id = request.POST.get("problem_id", None)

        try:
            pin = ObservationPinToProblem.objects.get(observation_id=observation_id, problem_id=problem_id)
            pin.delete();
        except ObservationPinToProblem.DoesNotExist:
            pin = ObservationPinToProblem(author=request.user.profile, observation_id=observation_id, problem_id=problem_id)
            pin.save()

        resp['pin'] = ObservationPinToProblemSerializer(pin).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
def add_new_data(request, patient_id, observation_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        effective_datetime = request.POST.get("datetime", None)
        if effective_datetime:
            effective_datetime = datetime.strptime(effective_datetime, '%m/%d/%Y %H:%M')
        value = request.POST.get("value", None)

        component = ObservationComponent(author=request.user.profile, observation_id=observation_id, effective_datetime=effective_datetime, value_quantity=value)
        component.save()

        resp['component'] = ObservationComponentSerializer(component).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_individual_data_info(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = ObservationComponent.objects.get(id=component_id)
        if not component.observation.name == OBSERVATION_TYPES['a1c']['name']:
            resp['info'] = ObservationComponentSerializer(component).data
            resp['success'] = True
    return ajax_response(resp)

@login_required
def delete_individual_data(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = ObservationComponent.objects.get(id=component_id)
        component.delete()
        resp['success'] = True
    return ajax_response(resp)

@login_required
def save_data(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        component = ObservationComponent.objects.get(id=component_id)
        
        effective_datetime = request.POST.get("datetime", None)
        if effective_datetime:
            effective_datetime = datetime.strptime(effective_datetime, '%m/%d/%Y %H:%M')
        value_quantity = request.POST.get("value_quantity", None)

        component.effective_datetime = effective_datetime
        component.value_quantity = value_quantity
        component.save()

        resp['info'] = ObservationComponentSerializer(component).data
        resp['success'] = True
    return ajax_response(resp)