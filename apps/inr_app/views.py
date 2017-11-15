from dateutil import parser, relativedelta
from dateutil.relativedelta import relativedelta

from common.views import *
from emr.models import Inr, InrTextNote, UserProfile, Medication, ObservationComponent, \
    ObservationPinToProblem, ToDo, ObservationValue
from medication_app.serializers import MedicationSerializer
from todo_app.serializers import TodoSerializer
from .serializers import InrTextNoteSerializer, InrSerializer, INRPatientSerializer
from .serializers import ProblemSerializer


@login_required
def get_inr_target(request, patient_id):
    """
    Get patient INR target goal
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    user_profile = UserProfile.objects.filter(user_id=patient_id).get()

    resp['target'] = user_profile.inr_target
    resp['success'] = True
    return ajax_response(resp)


@login_required
def set_inr_target(request, patient_id):
    """
    Set patient INR widget
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    UserProfile.objects.filter(user_id=patient_id).update(inr_target=int(json_body.get('value')))

    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_problems(request, patient_id):
    """
    Get all problems, whether this INR widget is pinned to
    Refer: https://trello.com/c/RzwrZPgU
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}

    # Find the observation component have LOINC code: 6301-6 -> reserve get observation -> get pinned problem
    # Each user should not have more than one(zero or one) observation which have LOINC code above
    patient = User.objects.filter(profile__id=int(patient_id)).first()
    observation_component = ObservationComponent.objects.filter(component_code='6301-6',
                                                                observation__subject=patient).get()

    observation_pin = ObservationPinToProblem.objects.filter(observation_id=observation_component.observation_id)
    problems = [observation_pin.problem for observation_pin in observation_pin]

    resp['problems'] = ProblemSerializer(problems, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_medications(request, patient_id):
    """
    Get all patient's medications in following set:  {375383004, 375379004, 375378007, 319735007, 375374009, 319734006, 375380001, 375375005, 319733000, 319736008}
    Refer: https://trello.com/c/Cts0FOSj
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    medications = Medication.objects.filter(patient_id=patient_id,
                                            concept_id__in={375383004, 375379004, 375378007, 319735007, 375374009,
                                                            319734006, 375380001, 375375005, 319733000, 319736008})

    resp['medications'] = MedicationSerializer(medications, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_inr_note(request, patient_id):
    """

    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    row = json_body.get('row')

    text_note_query_set = InrTextNote.objects.filter(patient_id=patient_id).order_by('-datetime')

    if 0 == row:
        resp['notes'] = InrTextNoteSerializer(text_note_query_set, many=True).data
    else:
        resp['note'] = InrTextNoteSerializer(text_note_query_set.first()).data

    resp['total'] = text_note_query_set.count()
    resp['success'] = True
    return ajax_response(resp)


@login_required
def add_note(request, patient_id):
    """
    Adding new note to INR widget
    Return newly added item & new total count
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    note = InrTextNote(note=json_body.get('note'), author=request.user.profile, patient_id=patient_id)
    note.save()

    resp['note'] = InrTextNoteSerializer(note).data
    resp['total'] = InrTextNote.objects.filter(patient_id=patient_id).count()
    resp['success'] = True

    return ajax_response(resp)


@login_required
def get_orders(request, patient_id, problem_id):
    """
    Get all orders(aka todo) which is generated in this widget
    :param problem_id:
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    orders = ToDo.objects.filter(patient_id=patient_id).filter(problem_id=problem_id).filter(accomplished=False).filter(
        created_at=1)

    resp['orders'] = TodoSerializer(orders, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def add_order(request, patient_id):
    """

    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    todo = json_body.get('todo')
    due_date = json_body.get('due_date')
    problem_id = json_body.get('problem_id')
    user_profile = UserProfile.objects.filter(id=patient_id).get()

    todo = ToDo(todo=todo, user=request.user,
                patient=user_profile.user,
                problem_id=problem_id,
                created_at=1,
                accomplished=False)
    if due_date is not None:
        todo.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
    todo.save()

    resp['order'] = TodoSerializer(todo).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_inr_table(request, patient_id):
    """
    Get the INR table(which stand for medication dosage of data point in INR data)
    :param request:
    :param patient_id:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    row = json_body.get('row')

    observation_value = ObservationValue.objects.filter(component__component_code='6301-6') \
        .filter(component__observation__subject_id=patient_id).order_by('-effective_datetime')

    if 0 == row:
        resp['inrs'] = InrSerializer(observation_value, many=True).data
    else:
        resp['inrs'] = InrSerializer(observation_value[:int(row)], many=True).data

    resp['success'] = True
    return ajax_response(resp)


@login_required
def add_inr(request, patient_id):
    """
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)

    date_measured = json_body.get('date_measured')
    current_dose = json_body.get('current_dose')
    inr_value = json_body.get('inr_value')
    new_dosage = json_body.get('new_dosage')
    next_inr = json_body.get('next_inr')
    patient = UserProfile.objects.filter(id=int(patient_id)).first().user
    observation_component = ObservationComponent.objects.filter(observation__subject=patient).filter(
        component_code='6301-6')

    if observation_component.exists():
        if date_measured is None:
            date_measured = datetime.now().strftime('%m/%d/%Y %H:%M')
        if next_inr is None:
            next_inr = (datetime.now() + relativedelta(months=+1)).strftime('%m/%d/%Y %H:%M')

        # 1st add observation value first
        observation_value = ObservationValue(author=request.user.profile, component_id=observation_component.get().id,
                                             effective_datetime=parser.parse(date_measured),
                                             value_quantity=inr_value)
        observation_value.save()

        last_dosage = Inr.objects.filter(patient_id=patient_id).order_by('observation_value__effective_datetime').last()
        if current_dose is None:
            current_dose = last_dosage.current_dose
        if new_dosage is None:
            new_dosage = last_dosage.new_dosage

        # 2nd add dosage
        dosage = Inr(observation_value=observation_value, patient_id=patient_id, author=request.user.profile,
                     current_dose=current_dose, new_dosage=new_dosage,
                     next_inr=parser.parse(next_inr))
        dosage.save()

        # Fetch data from DB to get
        resp['inr'] = InrSerializer(ObservationValue.objects.filter(id=observation_value.id).get()).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
def update_inr(request, patient_id):
    """
    :param request:
    :param patient_id:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    observation_value_id = json_body.get('id')
    date_measured = json_body.get('date_measured')
    current_dose = json_body.get('current_dose')
    inr_value = json_body.get('inr_value')
    new_dosage = json_body.get('new_dosage')
    next_inr = json_body.get('next_inr')  # Date time value

    # 1st update observation value first
    # Update primary info
    observation_value = ObservationValue.objects.select_related('inr').get(id=observation_value_id)

    # Permission checking
    if request.user.profile.role == 'patient' and observation_value.author != request.user.profile:
        return ajax_response(resp)

    observation_value.effective_datetime = parser.parse(date_measured)
    observation_value.value_quantity = inr_value
    observation_value.save()

    inr, created = Inr.objects.get_or_create(observation_value=observation_value)
    if created:
        inr.author = request.user.profile
        inr.patient_id = patient_id

    inr.current_dose = current_dose
    inr.new_dosage = new_dosage
    inr.next_inr = parser.parse(next_inr)
    inr.save()

    resp['inr'] = InrSerializer(observation_value.refresh_from_db()).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
def delete_inr(request, patient_id):
    """
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    observation_value_id = json_body.get('id')

    observation_value = ObservationValue.objects.filter(id=observation_value_id).get()
    # Patient can only delete item if they entered
    if request.user.profile.role == 'patient' and observation_value.author != request.user.profile:
        return ajax_response(resp)

    observation_value.delete()

    resp = {'success': True}
    return ajax_response(resp)


@login_required
def find_patient(request):
    """

    :param request:
    :return:
    """
    resp = {}
    json_body = json.loads(request.body)
    search_str = json_body.get('search_str')

    patients = UserProfile.objects.filter(role='patient').filter(
        Q(user__first_name__icontains=search_str)
        | Q(user__last_name__icontains=search_str)
    )

    resp['patients'] = INRPatientSerializer(patients, many=True).data
    return ajax_response(resp)
