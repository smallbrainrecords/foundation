from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import Observation, ObservationComponent, ObservationValueTextNote, ObservationOrder, \
    PhysicianTeam, PatientController, ObservationPinToProblem, Problem, ObservationUnit, ObservationValue
from emr.models import OBSERVATION_TYPES
from .serializers import ObservationValueTextNoteSerializer, ObservationComponentSerializer, \
    ObservationSerializer, ObservationPinToProblemSerializer, ObservationValueSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
from users_app.views import permissions_accessed


@login_required
def track_observation_click(request):
    resp = {}
    resp['success'] = False

    actor = request.user
    if request.POST.get("patient_id", None):
        patient = User.objects.get(id=request.POST.get("patient_id", None))

        if request.POST.get("observation_id", None):
            observation = Observation.objects.get(id=request.POST.get("observation_id", None))
            summary = "<b>%s</b> accessed %s" % (actor.username, observation.name)
        else:
            summary = "<b>%s</b> accessed data" % (actor.username)
        op_add_event(actor, patient, summary)
        resp['success'] = True

    return ajax_response(resp)


@login_required
def get_datas(request, patient_id):
    resp = {}
    resp['success'] = False

    if permissions_accessed(request.user, int(patient_id)):
        # add default datas: heart rate, blood pressure, respiratory rate, body temperature, height, weight, body mass index
        patient_user = User.objects.get(id=patient_id)
        for data in OBSERVATION_TYPES:
            if not data['name'] == 'a1c' and not Observation.objects.filter(name=data['name'], author=None,
                                                                            subject=patient_user.profile).exists():
                observation = Observation()
                observation.name = data['name']
                observation.subject = patient_user.profile
                observation.save()

                first_loop = True
                for unit in data['unit']:
                    observation_unit = ObservationUnit.objects.create(observation=observation, value_unit=unit)
                    if first_loop:
                        observation_unit.is_used = True  # will be changed in future when having conversion
                        first_loop = False
                    observation_unit.save()

                if data.has_key('components'):
                    for component in data['components']:
                        observation_component = ObservationComponent()
                        observation_component.observation = observation
                        observation_component.component_code = component['loinc_code']
                        observation_component.name = component['name']
                        observation_component.save()

                else:
                    observation_component = ObservationComponent()
                    observation_component.observation = observation
                    observation_component.component_code = data['loinc_code']
                    observation_component.name = data['name']
                    observation_component.save()

        observations = Observation.objects.filter(subject__user__id=int(patient_id))

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
@permissions_required(["add_data_type"])
@api_view(["POST"])
def add_new_data_type(request, patient_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        observation = Observation.objects.create(subject__user__id=int(patient_id),
                                                 author=request.user.profile,
                                                 name=request.POST.get("name", None),
                                                 color=request.POST.get("color", None))

        observation.save()

        unit = request.POST.get("unit", None)
        if unit:
            observation_unit = ObservationUnit.objects.create(observation=observation, value_unit=unit)
            observation_unit.is_used = True  # will be changed in future when having conversion
            observation_unit.save()

        observation_component = ObservationComponent()
        observation_component.observation = observation
        observation_component.component_code = request.POST.get("code", None)
        observation_component.name = request.POST.get("name", None)
        observation_component.save()

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
            pin = ObservationPinToProblem(author=request.user.profile, observation_id=observation_id,
                                          problem_id=problem_id)
            pin.save()

        resp['pin'] = ObservationPinToProblemSerializer(pin).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_new_data(request, patient_id, component_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        effective_datetime = request.POST.get("datetime", None)
        if effective_datetime:
            effective_datetime = datetime.strptime(effective_datetime, '%m/%d/%Y %H:%M')
        else:
            effective_datetime = datetime.now()
        value = request.POST.get("value", None)

        value = ObservationValue(author=request.user.profile, component_id=component_id,
                                 effective_datetime=effective_datetime, value_quantity=value)
        value.save()

        summary = "A value of <b>%s</b> was added for <b>%s</b>" % (
            value.value_quantity, value.component.observation.name)
        op_add_event(request.user, value.component.observation.subject.user, summary)

        resp['value'] = ObservationValueSerializer(value).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
def get_individual_data_info(request, patient_id, value_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        value = ObservationValue.objects.get(id=value_id)
        if not value.component.observation.name == OBSERVATION_TYPES[0]['name']:
            resp['info'] = ObservationValueSerializer(value).data
            resp['success'] = True
    return ajax_response(resp)


@login_required
def delete_individual_data(request, patient_id, value_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        value = ObservationValue.objects.get(id=value_id)
        value.delete()
        resp['success'] = True
    return ajax_response(resp)


@login_required
def save_data(request, patient_id, value_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        value = ObservationValue.objects.get(id=value_id)

        effective_datetime = request.POST.get("datetime", None)
        if effective_datetime:
            effective_datetime = datetime.strptime(effective_datetime, '%m/%d/%Y %H:%M')
        value_quantity = request.POST.get("value_quantity", None)

        value.effective_datetime = effective_datetime
        value.value_quantity = value_quantity
        value.save()

        resp['info'] = ObservationValueSerializer(value).data
        resp['success'] = True
    return ajax_response(resp)


@login_required
@permissions_required(["add_data_type"])
@api_view(["POST"])
def save_data_type(request, patient_id, observation_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        observation = Observation.objects.get(id=observation_id)
        if not observation.author == None:  # prevent default datas
            observation.name = request.POST.get("name", None)
            observation.color = request.POST.get("color", None)

            observation.save()

            # TODO: will be changed later if we have more components in one custom observation
            for component in observation.observation_components.all():
                component.name = request.POST.get("name", None)
                component.component_code = request.POST.get("code", None)
                component.save()

            unit = request.POST.get("unit", None)
            if unit:
                for observation_unit in observation.observation_units.all():
                    observation_unit.value_unit = unit
                    observation_unit.save()

            resp['observation'] = ObservationSerializer(observation).data
            resp['success'] = True

    return ajax_response(resp)


@login_required
@permissions_required(["add_data_type"])
@api_view(["POST"])
def delete_data(request, patient_id, observation_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        observation = Observation.objects.get(id=observation_id)
        if not observation.author == None:  # prevent default datas
            pins = ObservationPinToProblem.objects.filter(observation_id=observation_id)
            for pin in pins:
                pin.delete()

            for component in observation.observation_components.all():
                for value in component.observation_component_values.all():
                    value.delete()
                component.delete()

            observation.delete()

            resp['success'] = True

    return ajax_response(resp)

# TODO: AnhDN Check this working flow
@login_required
@permissions_required(["add_data_type"])
@api_view(["POST"])
def update_graph(request):
    resp = {}
    resp['success'] = False
    # If user have access to this data
    if permissions_accessed(request.user, int(request.POST.get('patient_id'))):
        observation = Observation.objects.get(id=request.POST.get('data_id'))
        observation.graph = request.POST.get('graph_type')
        observation.save()
        resp['success'] = True

    return ajax_response(resp)
