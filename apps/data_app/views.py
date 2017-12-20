import math

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from rest_framework.decorators import api_view

from common.views import *
from data_app.operations import get_observation_most_common_value
from emr.models import OBSERVATION_TYPES
from emr.models import Observation, ObservationComponent, ObservationOrder, \
    PhysicianTeam, ObservationPinToProblem, Problem, ObservationUnit, ObservationValue, \
    Inr, UserProfile
from emr.operations import op_add_event
from inr_app.serializers import InrSerializer
from users_app.views import permissions_accessed
from .serializers import ObservationSerializer, ObservationPinToProblemSerializer, ObservationValueSerializer


@login_required
def track_observation_click(request):
    resp = {'success': False}

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
    resp = {'success': False}

    if permissions_accessed(request.user, int(patient_id)):
        # TODO: This initial data should be added when a patient is REGISTERED | ACTIVED
        # Add default datas: heart rate, blood pressure, respiratory rate, body temperature, height, weight,
        # body mass index
        patient_user = User.objects.get(id=patient_id)
        for data in OBSERVATION_TYPES:
            if not data['name'] == 'a1c' and not Observation.objects.filter(name=data['name'], author=None,
                                                                            subject=patient_user).exists():
                observation = Observation()
                observation.name = data['name']
                observation.subject = patient_user
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

        observations = Observation.objects.filter(subject__id=int(patient_id))

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
    resp = {'success': True, 'info': ObservationSerializer(observation).data}
    return ajax_response(resp)


@login_required
@permissions_required(["add_data_type"])
@api_view(["POST"])
def add_new_data_type(request, patient_id):
    resp = {'success': False}
    name = request.POST.get("name", None)
    color_code = request.POST.get("color", None)
    unit = request.POST.get("unit", None)

    if permissions_accessed(request.user, int(patient_id)):
        patient = User.objects.get(id=int(patient_id))
        observation = Observation.objects.create(subject=patient, author=request.user, name=name, color=color_code)
        observation.save()

        if unit:
            observation_unit = ObservationUnit.objects.create(observation=observation, value_unit=unit)
            observation_unit.is_used = True  # will be changed in future when having conversion
            observation_unit.save()

        observation_component = ObservationComponent()
        observation_component.observation = observation
        observation_component.component_code = request.POST.get("code", None)
        observation_component.name = name
        observation_component.save()

        resp['observation'] = ObservationSerializer(observation).data
        resp['success'] = True

    return ajax_response(resp)


@permissions_required(["set_data_order"])
@login_required
def update_order(request):
    resp = {'success': False}

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
    resp = {'success': True, 'pins': ObservationPinToProblemSerializer(pins, many=True).data}
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def obseration_pin_to_problem(request, patient_id):
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)) or True:
        observation_id = request.POST.get("data_id", None)
        problem_id = request.POST.get("problem_id", None)
        observation = Observation.objects.get(id=observation_id)

        try:
            pin = ObservationPinToProblem.objects.get(observation_id=observation_id, problem_id=problem_id)
            up = UserProfile.objects.get(user_id=request.user.id)
            if up.role == 'patient' and pin.author_id != request.user.id:
                resp['success'] = "notallow"
                return ajax_response(resp)
            pin.delete()
            problems = Problem.objects.filter(patient_id=patient_id)
            optp = ObservationPinToProblem.objects.values_list('observation_id', ).filter(problem__in=problems)
            optp1 = []
            for x in optp:
                optp1.append(x[0])
            component = ObservationComponent.objects.filter(observation_id__in=optp1, component_code='6301-6')
            if ObservationComponent.objects.filter(observation=observation, component_code='6301-6').exists() and len(
                    component) < 1:
                if Inr.objects.filter(observation_id=observation_id).exists():
                    Inr.objects.filter(observation_id=observation_id).delete()
                    resp['remove_inr'] = True
        except ObservationPinToProblem.DoesNotExist:
            problems = Problem.objects.filter(patient_id=patient_id)
            optp = ObservationPinToProblem.objects.values_list('observation_id', ).filter(
                problem__in=problems).distinct()
            optp1 = []
            for x in optp:
                optp1.append(x[0])
            component = ObservationComponent.objects.filter(observation_id__in=optp1, component_code='6301-6')
            pin = ObservationPinToProblem(author_id=request.user.id, observation_id=observation_id,
                                          problem_id=problem_id)
            pin.save()
            if ObservationComponent.objects.filter(observation=observation, component_code='6301-6').exists() and len(
                    component) < 1:
                patient_user = User.objects.get(id=patient_id)
                inr = Inr(observation_id=observation_id, problem_id=problem_id, author=request.user,
                          patient=patient_user)
                inr.save()
                resp['inr'] = InrSerializer(inr).data

        resp['pin'] = ObservationPinToProblemSerializer(pin).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_new_data(request, patient_id, component_id):
    resp = {'success': False}
    # Patient user instance
    patient = UserProfile.objects.filter(id=int(patient_id)).first().user

    if permissions_accessed(request.user, int(patient_id)):
        # Get user submit data
        effective_datetime = request.POST.get("datetime", datetime.now())
        if effective_datetime:
            effective_datetime = datetime.strptime(effective_datetime, '%m/%d/%Y %H:%M')
        valueQuantity = request.POST.get("value", None)

        # DB stuff
        value = ObservationValue(author=request.user, component_id=component_id,
                                 effective_datetime=effective_datetime, value_quantity=valueQuantity)
        value.save()

        # Auto add bmi data if observation component is weight or height
        # TODO: Need to improve this block of code - https://trello.com/c/PaSdgs3k
        bmiComponent = ObservationComponent.objects.filter(component_code='39156-5').filter(
            observation__subject=patient).first()
        #  TODO: Later when finished refactor model relationship and patient
        if value.component.name == 'weight':
            # Calculation
            heightComponent = ObservationComponent.objects.filter(component_code='8302-2').filter(
                observation__subject=patient).get()
            height = get_observation_most_common_value(heightComponent, effective_datetime)
            bmiValue = round(float(value.value_quantity) * 703 / math.pow(height, 2), 2)

            # DB stuff transaction
            ObservationValue(author=request.user, component=bmiComponent,
                             effective_datetime=effective_datetime, value_quantity=bmiValue).save()
            # Save log
            summary = "A value of <b>{0}</b> was added for <b>{1}</b>".format(bmiValue, bmiComponent.observation.name)
            op_add_event(request.user, value.component.observation.subject, summary)

        if value.component.name == 'height':
            # Calculation
            weightComponent = ObservationComponent.objects.filter(component_code='3141-9').filter(
                observation__subject=patient).get()
            weight = get_observation_most_common_value(weightComponent, effective_datetime)
            bmiValue = round(weight * 703 / math.pow(float(value.value_quantity), 2), 2)

            # DB stuff transaction
            ObservationValue(author=request.user, component=bmiComponent,
                             effective_datetime=effective_datetime, value_quantity=bmiValue).save()
            # Save log
            summary = "A value of <b>{0}</b> was added for <b>{1}</b>".format(bmiValue, bmiComponent.observation.name)
            op_add_event(request.user, value.component.observation.subject, summary)

        # Save log
        summary = "A value of <b>{0}</b> was added for <b>{1}</b>".format(value.value_quantity,
                                                                          value.component.observation.name)
        op_add_event(request.user, value.component.observation.subject, summary)

        resp['value'] = ObservationValueSerializer(value).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
def get_individual_data_info(request, patient_id, value_id):
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)):
        value = ObservationValue.objects.get(id=value_id)
        if not value.component.observation.name == OBSERVATION_TYPES[0]['name']:
            resp['info'] = ObservationValueSerializer(value).data
            resp['success'] = True
    return ajax_response(resp)


@login_required
def delete_individual_data(request, patient_id, value_id):
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)):
        value = ObservationValue.objects.get(id=value_id)
        value.delete()
        resp['success'] = True
    return ajax_response(resp)


@login_required
def save_data(request, patient_id, value_id):
    resp = {'success': False}
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
    resp = {'success': False}
    name = request.POST.get("name", None)
    color_code = request.POST.get("color", None)
    unit = request.POST.get("unit", None)
    if permissions_accessed(request.user, int(patient_id)):
        observation = Observation.objects.get(id=observation_id)
        if observation.author is not None:  # prevent default datas
            observation.name = name
            observation.color = color_code
            observation.save()

            # TODO: will be changed later if we have more components in one custom observation
            for component in observation.observation_components.all():
                component.name = name
                component.component_code = request.POST.get("code", None)
                component.save()

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
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)):
        observation = Observation.objects.get(id=observation_id)
        if not observation.author is None:  # prevent default datas
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


@login_required
@permissions_required(["add_data_type"])
@api_view(["POST"])
def update_graph(request):
    resp = {'success': False}
    # If user have access to this data
    if permissions_accessed(request.user, int(request.POST.get('patient_id'))):
        observation = Observation.objects.get(id=request.POST.get('data_id'))
        observation.graph = request.POST.get('graph_type')
        observation.save()
        resp['success'] = True

    return ajax_response(resp)


@login_required
def delete_component_values(request, patient_id):
    """
    Delete observation component values    
    :param patient_id: 
    :param request: 
    :return: 
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    observation_value_ids = json_body.get('component_values')

    if permissions_accessed(request.user, int(patient_id)):
        ObservationValue.objects.filter(id__in=observation_value_ids).delete()
        resp['success'] = True
    return ajax_response(resp)
