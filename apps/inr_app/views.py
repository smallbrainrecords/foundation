from struct import pack

from rest_framework.decorators import api_view

from common.views import *
from emr.models import Inr, InrValue, InrTextNote, Problem, UserProfile, Medication, Observation, ObservationComponent, \
    ObservationPinToProblem, BELONG_TO, ToDo
from medication_app.serializers import MedicationSerializer
from todo_app.serializers import TodoSerializer
from users_app.views import permissions_accessed
from .serializers import InrTextNoteSerializer, InrSerializer
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
    observation_component = ObservationComponent.objects.filter(component_code='6301-6',
                                                                observation__subject_id=patient_id).get()

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
def get_orders(request, patient_id):
    """
    Get all orders(aka todo) which is generated in this widget
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    orders = ToDo.objects.filter(patient_id=patient_id).filter(accomplished=False).filter(created_at=1)

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
    # problem_id = json_body.get('problem_id')
    user_profile = UserProfile.objects.filter(id=patient_id).get()

    todo = ToDo(todo=todo, due_date=datetime.strptime(due_date, '%Y-%m-%d').date(),
                user=request.user,
                patient=user_profile.user,
                accomplished=False, created_at=1)
    todo.save()

    resp['order'] = TodoSerializer(todo).data
    resp['success'] = True
    return ajax_response(resp)


# DEPRECATED ITEMS. UNUSED OR WILL BE REMOVED

@login_required
def get_inrs(request, patient_id, problem_id):
    """
    Get the INR widget which is pinned to the problem(sharing problem is filtered through patient)
    :param request:
    :param patient_id:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    if permissions_accessed(request.user, int(patient_id)):
        inr = Inr.objects.filter(problem__id=problem_id, patient_id=patient_id)

    resp['success'] = True
    if inr.exists():
        resp['info'] = InrSerializer(inr.get()).data
    return ajax_response(resp)


@login_required
def set_target(request, inr_id):
    resp = {}
    resp['success'] = True
    try:
        Inr.objects.filter(id=inr_id).update(target=request.GET['target'])
    except:
        resp['success'] = False
    return ajax_response(resp)


@login_required
@api_view(['GET'])
def get_list_problem(request):
    resp = {}
    resp['success'] = True
    # problem = Problem.objects.filter(inr_id=request.GET['id'])
    problem = Problem.objects.filter(id__in=Inr.objects.values('problem_id'))
    resp['data'] = ProblemSerializer(problem, many=True).data
    return ajax_response(resp)


@login_required
@api_view(['POST'])
def save_inrvalue(request):
    resp = {}
    resp['success'] = True
    inrvalue = InrValue(effective_datetime=request.POST['effective_datetime'],
                        current_dose=request.POST['current_dose'], value=float(request.POST['value']),
                        new_dosage=request.POST['new_dosage'], next_inr=request.POST['next_inr'],
                        inr_id=int(request.POST['inr']), author_id=int(request.POST['author_id']), ispatient=True)
    try:
        inrvalue.save()
        resp['id'] = inrvalue.pk
    except:
        resp['success'] = False
    return ajax_response(resp)


@login_required
@api_view(['POST'])
def edit_inrvalue(request, inr_id):
    resp = {}
    resp['success'] = True
    try:
        InrValue.objects.filter(id=inr_id, ispatient=True).update(
            effective_datetime=request.POST['effective_datetime'],
            current_dose=request.POST['current_dose'],
            value=float(request.POST['value']),
            new_dosage=request.POST['new_dosage'],
            next_inr=request.POST['next_inr'])
    except:
        resp['success'] = False
    return ajax_response(resp)


@login_required
@api_view(['GET'])
def delete_inrvalue(request, inr_id):
    resp = {}
    resp['success'] = True
    try:
        InrValue.objects.get(id=inr_id, ispatient=True).delete()
    except:
        resp['success'] = False
    return ajax_response(resp)
