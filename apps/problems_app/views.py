"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from datetime import timedelta

from dateutil import parser
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from document_app.serializers import DocumentSerializer
from encounters_app.serializers import EncounterSerializer

try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps

import operator

from a1c_app.serializers import AOneCSerializer
from colons_app.serializers import ColonCancerScreeningSerializer
from common.views import *
from data_app.serializers import (
    ObservationPinToProblemSerializer,
    ObservationSerializer,
)
from django.db.models import Max, Prefetch, Q
from django.shortcuts import get_object_or_404
from emr.models import (
    AOneC,
    ColonCancerScreening,
    CommonProblem,
    Encounter,
    Goal,
    Label,
    LabeledProblemList,
    MedicationPinToProblem,
    Observation,
    ObservationComponent,
    ObservationPinToProblem,
    ObservationUnit,
    PatientController,
    PatientImage,
    PhysicianTeam,
    Problem,
    ProblemActivity,
    ProblemLabel,
    ProblemNote,
    ProblemOrder,
    ProblemRelationship,
    SharingPatient,
    TaggedToDoOrder,
    ToDo,
    UserProfile,
)
from emr.operations import op_add_event, op_add_todo_event
from goals_app.serializers import GoalSerializer
from medication_app.serializers import MedicationPinToProblemSerializer
from problems_app.operations import (
    add_problem_activity,
    check_problem_access,
    get_available_widget,
)
from problems_app.services import ProblemService
from rest_framework.decorators import api_view
from todo_app.operations import add_todo_activity
from todo_app.serializers import TodoSerializer
from users_app.serializers import UserProfileSerializer

from .serializers import (
    CommonProblemSerializer,
    LabeledProblemListSerializer,
    PatientImageSerializer,
    ProblemActivitySerializer,
    ProblemInfoSerializer,
    ProblemLabelSerializer,
    ProblemNoteSerializer,
    ProblemSerializer,
    ProblemTodoSerializer,
)


@login_required
#@timeit
def track_problem_click(request, problem_id):
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    if actor_profile.role in ['physician', 'admin']:
        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        summary = "Clicked <u>problem</u>: <b>%s</b>" % problem.problem_name
        op_add_event(actor, patient, summary)

        activity = "Visited <u>problem</u>: <b>%s</b>" % problem.problem_name
        add_problem_activity(problem, request.user, activity)

    resp = {}
    return ajax_response(resp)


@login_required
#@timeit
def get_problem_info(request, problem_id):
    """
    Loading problem details
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}
    sharing_patients_list = []

    problem_info = Problem.objects.select_related("patient").get(id=problem_id)
    hasProblemAccess = check_problem_access(request.user, problem_info)

    # Loading sharing patient list
    sharing_patients = SharingPatient.objects.filter(
        shared=problem_info.patient).order_by('sharing__first_name', 'sharing__last_name')
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        user_dict['problems'] = [x.id for x in sharing_patient.problems.all()]
        sharing_patients_list.append(user_dict)

    if hasProblemAccess:
        resp = {
            'success': True,
            'info': ProblemInfoSerializer(problem_info).data,
            'available_widgets': get_available_widget(problem_info),
            'sharing_patients': sharing_patients_list
        }

    return ajax_response(resp)


@login_required
#@timeit
def get_a1c(request, problem_id):
    """
    A1C load todo is not accomplished only
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}
    a1c = AOneC.objects.filter(problem__id=problem_id).get()
    a1c.a1c_todos.set(a1c.a1c_todos.filter(accomplished=False))

    resp['success'] = True
    resp['a1c'] = AOneCSerializer(a1c).data
    return ajax_response(resp)


@login_required
#@timeit
def get_colon_cancers(request, problem_id):
    """
    Get problem colon cancer widget
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    colon_cancers = ColonCancerScreening.objects.filter(problem__id=problem_id).get()
    # colon_cancers.colon_cancer_todos = colon_cancers.colon_cancer_todos.filter(accomplished=False)
    colon_cancers.colon_cancer_todos.set(colon_cancers.colon_cancer_todos.filter(accomplished=False))

    resp['success'] = True
    resp['colon_cancers'] = ColonCancerScreeningSerializer(colon_cancers).data
    return ajax_response(resp)


@login_required
#@timeit
def get_problem_activity(request, problem_id, last_id):
    resp = {'success': False}

    problem = get_object_or_404(Problem, pk=problem_id)
    activities = ProblemActivity.objects.filter(problem=problem).filter(id__gt=last_id)
    activity_holder = ProblemActivitySerializer(activities, many=True).data

    resp['activities'] = activity_holder
    resp['success'] = True
    return ajax_response(resp)


# Problem
@permissions_required(["add_problem"])
@login_required
@api_view(["POST"])
#@timeit
def add_patient_problem(request, patient_id):
    resp = {'success': False}
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    term = request.POST.get('term')
    concept_id = request.POST.get('code', None)
    physician = request.user
    patient = User.objects.get(id=int(patient_id))

    if Problem.objects.filter(problem_name=term, patient__id=patient_id).exists():
        resp["msg"] = "Problem already being added"
        return ajax_response(resp)

    new_problem = Problem.objects.create_new_problem(patient_id, term, concept_id, actor_profile)

    # https://trello.com/c/0OlwGwCB
    # Only add if problem is diabetes and patient have not
    if "44054006" == concept_id:
        if not ObservationComponent.objects.filter(component_code="2345-7", observation__subject=patient).exists():
            # Add data(observation) Glucose type
            observation = Observation.objects.create(subject=patient, author=request.user, name="Glucose",
                                                     code="2345-7", color="#FFD2D2")
            observation.save()

            #  Add data unit
            observation_unit = ObservationUnit.objects.create(observation=observation, value_unit="mg/dL")
            observation_unit.is_used = True  # will be changed in future when having conversion
            observation_unit.save()

            #  Add data component
            observation_component = ObservationComponent()
            observation_component.observation = observation
            observation_component.component_code = "2345-7"
            observation_component.name = "Glucose"
            observation_component.save()
        else:
            observation = ObservationComponent.objects.get(component_code="2345-7", observation__subject=patient)
        # Pin to problem
        ObservationPinToProblem.objects.create(author_id=request.user.id, observation=observation, problem=new_problem)

    # Event
    summary = "Added <u>problem</u> <b>{}</b>".format(term)
    op_add_event(physician, new_problem.patient, summary, new_problem)

    # Activity
    activity = "Added <u>problem</u>: <b>{}</b>".format(term)
    add_problem_activity(new_problem, request.user, activity)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(new_problem).data
    return ajax_response(resp)


@permissions_required(["add_problem"])
@login_required
#@timeit
def add_patient_common_problem(request, patient_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    cproblem = request.POST.get('cproblem')
    problem_type = request.POST.get('type')

    problem = CommonProblem.objects.get(id=cproblem)

    if Problem.objects.filter(problem_name=problem.problem_name, concept_id=problem.concept_id,
                              patient__id=patient_id).exists():
        return ajax_response({"msg": "Problem already added"})

    new_problem = Problem.objects.create_new_problem(patient_id, problem.problem_name, problem.concept_id,
                                                     actor_profile)
    physician = request.user

    summary = 'Added <u>problem</u> <b>%s</b>' % problem.problem_name
    op_add_event(physician, new_problem.patient, summary, new_problem)
    activity = "Added <u>problem</u>: <b>%s</b>" % problem.problem_name
    add_problem_activity(new_problem, request.user, activity)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(new_problem).data
    return ajax_response(resp)


@permissions_required(["change_problem_name"])
@login_required
@api_view(["POST"])
#@timeit
def change_name(request, problem_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    term = request.POST.get('term')
    concept_id = request.POST.get('code', None)

    problem = Problem.objects.get(id=problem_id)
    if Problem.objects.filter(problem_name=term, patient=problem.patient).exists():
        return ajax_response({"msg": "Problem already added"})

    old_problem_concept_id = problem.concept_id
    old_problem_name = problem.problem_name
    if datetime.now() > datetime.strptime(
            problem.start_date.strftime('%d/%m/%Y') + ' ' + problem.start_time.strftime('%H:%M:%S'),
            "%d/%m/%Y %H:%M:%S") + timedelta(hours=24):
        problem.old_problem_name = old_problem_name

    problem.problem_name = term
    problem.concept_id = concept_id
    problem.save()

    physician = request.user

    if old_problem_concept_id and problem.concept_id:
        summary = '<b>%s (%s)</b> was changed to <b>%s (%s)</b>' % (
            old_problem_name, old_problem_concept_id, problem.problem_name, problem.concept_id)
    elif old_problem_concept_id:
        summary = '<b>%s (%s)</b> was changed to <b>%s</b>' % (
            old_problem_name, old_problem_concept_id, problem.problem_name)
    elif problem.concept_id:
        summary = '<b>%s</b> was changed to <b>%s (%s)</b>' % (
            old_problem_name, problem.problem_name, problem.concept_id)
    else:
        summary = '<b>%s</b> was changed to <b>%s</b>' % (old_problem_name, problem.problem_name)

    op_add_event(physician, problem.patient, summary, problem)
    add_problem_activity(problem, request.user, summary)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(problem).data

    return ajax_response(resp)


# Problems
@login_required
@api_view(["POST"])
#@timeit
def update_problem_status(request, problem_id):
    resp = {'success': False}

    # Different permissions for different cases
    # Modify this view

    actor_profile = UserProfile.objects.get(user=request.user)

    is_controlled = request.POST.get('is_controlled') == 'true'
    is_active = request.POST.get('is_active') == 'true'
    authenticated = request.POST.get('authenticated') == 'true'

    problem = Problem.objects.select_related("patient").get(id=problem_id)
    problem.is_controlled = is_controlled
    problem.is_active = is_active
    problem.authenticated = authenticated
    problem.save()

    status_labels = {
        'problem_name': problem.problem_name,
        'is_controlled': "controlled" if is_controlled else "not controlled",
        "is_active": "active" if is_active else "not_active",
        "authenticated": "authenticated" if authenticated else "not_authenticated",
    }

    physician = request.user

    summary = """Changed <u>problem</u>: <b>%(problem_name)s</b> status to : <b>%(is_controlled)s</b> ,<b>%(is_active)s</b> ,<b>%(authenticated)s</b>""" % status_labels
    op_add_event(physician, problem.patient, summary, problem)
    activity = summary
    add_problem_activity(problem, request.user, activity)

    resp['success'] = True
    return ajax_response(resp)


# Problems
@permissions_required(["modify_problem"])
@login_required
@api_view(["POST"])
#@timeit
def update_start_date(request, problem_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    start_date = request.POST.get('start_date')
    problem = Problem.objects.get(id=problem_id)
    problem.start_date = get_new_date(start_date)
    problem.save()

    physician = request.user
    patient = problem.patient
    summary = '''Changed <u>problem</u> : <b>%s</b> start date to <b>%s</b>''' % (
        problem.problem_name, problem.start_date)
    op_add_event(physician, patient, summary, problem)
    activity = summary
    add_problem_activity(problem, request.user, activity)

    resp['success'] = True
    return ajax_response(resp)


# Add History Note
@permissions_required(["modify_problem"])
@login_required
@api_view(["POST"])
#@timeit
def add_history_note(request, problem_id):
    resp = {'success': False}
    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        return ajax_response(resp)

    # Get params
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    note = request.POST.get('note')
    physician = request.user
    patient = problem.patient

    # Save note
    new_note = ProblemNote.objects.create_history_note(actor, problem, note)

    # Save problem log
    activity = "Added History Note  <b>{}</b>".format(note)
    add_problem_activity(problem, request.user, activity, 'input')

    # Save system log
    op_add_event(physician, patient, activity, problem)

    # https://trello.com/c/hkdbHZjw
    auto_generate_note_todo(actor_profile, patient, problem, request, resp)

    # Build response
    resp['success'] = True
    resp['note'] = ProblemNoteSerializer(new_note).data

    return ajax_response(resp)


#@timeit
def auto_generate_note_todo(actor_profile, patient, problem, request, resp):
    if 'patient' == actor_profile.role or 'nurse' == actor_profile.role or 'secretary' == actor_profile.role:
        # Create todo and Pin to problem
        note_auto_generated_todo = ToDo(patient=patient, problem=problem, todo="A note was added")
        order = ToDo.objects.all().aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        note_auto_generated_todo.order = order
        note_auto_generated_todo.save()

        summary = '''Added <u>todo</u> <a href="#/todo/{}"><b>{}</b></a> for <u>problem</u> <b>{}</b>'''.format(
            note_auto_generated_todo.id, "A note was added", problem.problem_name)
        op_add_todo_event(request.user, patient, summary, note_auto_generated_todo)

        add_todo_activity(note_auto_generated_todo, request.user, "Added this todo.")

        # Tag associated physician
        # Find all associated physician(s) with this patient
        patient_controller = PatientController.objects.filter(patient=patient).all()
        for doctor in patient_controller:
            TaggedToDoOrder.objects.create(todo=note_auto_generated_todo, user=doctor.physician)
            log = "<b>{0} {1} - {2}</b> joined this todo.".format(doctor.physician.first_name,
                                                                  doctor.physician.last_name,
                                                                  doctor.physician.profile.role)
            add_todo_activity(note_auto_generated_todo, request.user, log)

            resp['todo'] = TodoSerializer(note_auto_generated_todo).data


# Add Wiki Note
@login_required
#@timeit
def add_wiki_note(request, problem_id):
    """
    @depre
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    try:
        problem = Problem.objects.get(id=problem_id)
        author_profile = UserProfile.objects.get(user=request.user)
    except (Problem.DoesNotExist, UserProfile.DoesNotExist) as e:
        return ajax_response(resp)

    # Check if user is able to view patient
    # Todo
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    note = request.POST.get('note')
    physician = request.user
    patient = problem.patient

    new_note = ProblemNote.objects.create_wiki_note(request.user, problem, note)

    activity = 'Added wiki note: <b>%s</b>' % note
    add_problem_activity(problem, request.user, activity, 'input')

    op_add_event(physician, patient, activity, problem)

    # https://trello.com/c/hkdbHZjw
    auto_generate_note_todo(actor_profile, patient, problem, request, resp)

    resp['note'] = ProblemNoteSerializer(new_note).data
    resp['success'] = True

    return ajax_response(resp)

@permissions_required(["add_goal"])
@login_required
#@timeit
def add_problem_goal(request, problem_id):
    resp = {'success': False}

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    problem = Problem.objects.get(id=problem_id)
    patient = problem.patient

    goal = request.POST.get('name')

    new_goal = Goal(patient=patient, problem=problem, goal=goal)
    new_goal.save()

    physician = request.user

    summary = '''Added <u> goal </u> : <b>%s</b> to <u>problem</u> : <b>%s</b>''' % (goal, problem.problem_name)
    op_add_event(physician, patient, summary, problem)

    activity = summary
    add_problem_activity(problem, request.user, activity, 'output')

    resp['success'] = True
    resp['goal'] = GoalSerializer(new_goal).data
    return ajax_response(resp)


# Problems
@permissions_required(["add_todo"])
@login_required
#@timeit
def add_problem_todo(request, problem_id):
    resp = {'success': False}

    problem = Problem.objects.get(id=problem_id)
    actor_profile = UserProfile.objects.get(user=request.user)
    problem.authenticated = actor_profile.role in ['physician', 'admin']
    problem.save()

    patient = problem.patient

    todo = request.POST.get('name')
    due_date = request.POST.get('due_date', None)
    if due_date:
        due_date = parser.parse(due_date, dayfirst=False, ignoretz=True)
        # due_date = datetime.strptime(due_date, '%m/%d/%Y').date()

    new_todo = ToDo(patient=patient, problem=problem, todo=todo, due_date=due_date)

    a1c_id = request.POST.get('a1c_id', None)
    if a1c_id:
        a1c = AOneC.objects.get(id=int(a1c_id))
        new_todo.a1c = a1c

    order = ToDo.objects.all().aggregate(Max('order'))
    if not order['order__max']:
        order = 1
    else:
        order = order['order__max'] + 1
    new_todo.order = order
    new_todo.save()

    colon_cancer_id = request.POST.get('colon_cancer_id', None)
    if colon_cancer_id:
        colon = ColonCancerScreening.objects.get(id=int(colon_cancer_id))
        if not Label.objects.filter(name="screening", css_class="todo-label-yellow", is_all=True).exists():
            label = Label(name="screening", css_class="todo-label-yellow", is_all=True)
            label.save()
        else:
            label = Label.objects.get(name="screening", css_class="todo-label-yellow", is_all=True)
        new_todo.colon_cancer = colon
        new_todo.save()
        new_todo.labels.add(label)

    physician = request.user

    summary = '''Added <u>todo</u> : <a href="#/todo/%s"><b>%s</b></a> to <u>problem</u> : <b>%s</b>''' % (
        new_todo.id, todo, problem.problem_name)
    op_add_event(physician, patient, summary, problem)

    activity = summary
    add_problem_activity(problem, request.user, activity, 'output')

    summary = '''Added <u>todo</u> <a href="#/todo/%s"><b>%s</b></a> for <u>problem</u> <b>%s</b>''' % (
        new_todo.id, new_todo.todo, problem.problem_name)
    op_add_todo_event(physician, patient, summary, new_todo, True)
    # todo activity
    activity = '''
        Added this todo.
    '''
    add_todo_activity(new_todo, request.user, activity)

    resp['success'] = True
    resp['todo'] = TodoSerializer(new_todo).data
    return ajax_response(resp)


# Problems
@permissions_required(["add_problem_image"])
@login_required
@api_view(["POST"])
#@timeit
def upload_problem_image(request, problem_id):
    resp = {'success': False}
    actor_profile = UserProfile.objects.get(user=request.user)
    problem = Problem.objects.get(id=problem_id)
    problem.authenticated = actor_profile.role in ['physician', 'admin']
    problem.save()

    patient = problem.patient
    images = request.FILES
    image_holder = []
    for dict in images:
        image = request.FILES[dict]
        patient_image = PatientImage(patient=patient, problem=problem, image=image)
        patient_image.save()

        activity = summary = '''
        Physician added <u>image</u> to <u>problem</u> <b>%s</b> <br/><a href="/media/%s">
        <img src="/media/%s" class="thumbnail thumbnail-custom" /></a>
        ''' % (problem.problem_name, patient_image.image, patient_image.image)

        op_add_event(request.user, patient, summary, problem)
        add_problem_activity(problem, request.user, activity, 'input')

        image_holder.append(patient_image)

    resp['images'] = PatientImageSerializer(image_holder, many=True).data
    resp['success'] = True
    return ajax_response(resp)


# Problems
@permissions_required(["relate_problem"])
@login_required
@api_view(["POST"])
#@timeit
def delete_problem_image(request, problem_id, image_id):
    resp = {'success': False}

    actor_profile = UserProfile.objects.get(user=request.user)
    PatientImage.objects.get(id=image_id).delete()

    problem = Problem.objects.select_related("patient").get(id=problem_id)
    patient = problem.patient
    physician = request.user
    summary = '''Deleted <u>image</u> from <u>problem</u> : <b>%s</b>''' % problem.problem_name
    op_add_event(physician, patient, summary, problem)
    activity = summary
    add_problem_activity(problem, request.user, activity, 'input')

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["relate_problem"])
@login_required
@api_view(["POST"])
#@timeit
def relate_problem(request):
    resp = {'success': False}

    actor_profile = UserProfile.objects.get(user=request.user)
    relationship = request.POST.get('relationship') == 'true'
    source_id = request.POST.get('source_id', None)
    target_id = request.POST.get('target_id', None)

    source = Problem.objects.get(id=source_id)
    target = Problem.objects.get(id=target_id)
    activity = None

    if relationship:
        try:
            problem_relationship = ProblemRelationship.objects.get(source=source, target=target)
        except ProblemRelationship.DoesNotExist:
            problem_relationship = ProblemRelationship.objects.create(source=source, target=target)
            activity = '''Created Problem Relationship: <b>%s</b> effects <b>%s</b>''' % (
                source.problem_name, target.problem_name)
    else:
        ProblemRelationship.objects.get(source=source, target=target).delete()
        activity = '''Removed Problem Relationship: <b>%s</b> effects <b>%s</b>''' % (
            source.problem_name, target.problem_name)

    if activity:
        add_problem_activity(source, request.user, activity)
        add_problem_activity(target, request.user, activity)
        op_add_event(request.user, source.patient, activity)

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["modify_problem"])
@login_required
#@timeit
def update_by_ptw(request):
    resp = {'success': False}
    actor_profile = UserProfile.objects.get(user=request.user)

    timeline_data = json.loads(request.body)['timeline_data']
    for problem_json in timeline_data['problems']:
        problem = ProblemService.update_from_timeline_data(problem_json)
        patient = problem.patient
        problem.authenticated = actor_profile.role in ['physician', 'admin']
        problem.save()

        physician = request.user
        summary = '''Changed <u>problem</u> :<b>%s</b> start date to <b>%s</b>''' % (
            problem.problem_name, problem.start_date)
        op_add_event(physician, patient, summary, problem)
        activity = summary
        add_problem_activity(problem, request.user, activity)

        resp['success'] = True

    return ajax_response(resp)


@permissions_required(["modify_problem"])
@login_required
#@timeit
def update_state_to_ptw(request):
    resp = {'success': False}
    timeline_data = json.loads(request.body)['timeline_data']
    for problem_json in timeline_data['problems']:
        problem = ProblemService.update_from_timeline_data(problem_json)
        resp['success'] = True
    return ajax_response(resp)


@permissions_required(["set_problem_order"])
@login_required
#@timeit
def update_order(request):
    resp = {'success': False}

    datas = json.loads(request.body)
    if datas.has_key('patient_id'):
        id_problems = datas['problems']
        patient_id = datas['patient_id']
        try:
            problem = ProblemOrder.objects.get(user=request.user, patient_id=patient_id)
        except ProblemOrder.DoesNotExist:
            problem = ProblemOrder(user=request.user, patient_id=patient_id)
            problem.save()

        problem.order = id_problems
        problem.save()

    # list todo
    if datas.has_key('list_id'):
        list_id = datas['list_id']
        labeled_list = LabeledProblemList.objects.get(id=int(list_id))
        labeled_list.problem_list = datas['problems']
        labeled_list.save()

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def new_problem_label(request, problem_id):
    resp = {'success': False, 'status': False, 'new_status': False}

    name = request.POST.get('name')
    css_class = request.POST.get('css_class')

    problem = Problem.objects.get(id=problem_id)
    label = ProblemLabel.objects.filter(name=name, css_class=css_class, author=request.user,
                                        patient=problem.patient).first()
    if not label:
        label = ProblemLabel(name=name, css_class=css_class, author=request.user, patient=problem.patient)
        label.save()
        resp['new_status'] = True
        resp['new_label'] = ProblemLabelSerializer(label).data

    if not label in problem.labels.all():
        problem.labels.add(label)
        resp['status'] = True
        resp['label'] = ProblemLabelSerializer(label).data

    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def get_problem_labels(request, patient_id, user_id):
    labels = ProblemLabel.objects.filter(patient_id=patient_id, author_id=user_id)
    resp = {
        'labels': ProblemLabelSerializer(labels, many=True).data
    }
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def save_edit_problem_label(request, label_id, patient_id, user_id):
    resp = {'success': False, 'status': False}

    name = request.POST.get('name')
    css_class = request.POST.get('css_class')

    label = ProblemLabel.objects.get(id=label_id)

    if not ProblemLabel.objects.filter(name=name, css_class=css_class, patient_id=patient_id, author_id=user_id):
        label.name = name
        label.css_class = css_class
        label.save()
        resp['status'] = True

    resp['label'] = ProblemLabelSerializer(label).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def add_problem_label(request, label_id, problem_id):
    resp = {'success': False}

    problem = Problem.objects.get(id=problem_id)
    label = ProblemLabel.objects.get(id=label_id)
    problem.labels.add(label)

    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def remove_problem_label(request, label_id, problem_id):
    resp = {'success': False}

    problem = Problem.objects.get(id=problem_id)
    label = ProblemLabel.objects.get(id=label_id)
    problem.labels.remove(label)

    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def delete_problem_label(request, label_id):
    resp = {'success': False}

    ProblemLabel.objects.get(id=label_id).delete()

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def add_problem_list(request, patient_id, user_id):
    resp = {'success': False}

    data = json.loads(request.body)
    list_name = data['name']
    labels = data['labels']

    problem_labels = ProblemLabel.objects.filter(id__in=[label["id"] for label in labels])
    problems = Problem.objects.filter(labels__in=problem_labels).distinct().order_by('start_date')
    problems_holder = ProblemSerializer(problems, many=True).data
    ProblemService.populate_multiplicity(problems_holder)
    problems_holder = sorted(problems_holder, key=operator.itemgetter('multiply'), reverse=True)

    labeled_problems = LabeledProblemList.objects.create(user_id=user_id, name=list_name, patient_id=patient_id)
    for label in problem_labels:
        labeled_problems.labels.add(label)
    new_list_dict = LabeledProblemListSerializer(labeled_problems).data
    new_list_dict['problems'] = problems_holder

    resp = {
        'new_list': new_list_dict,
        'success': True
    }
    return ajax_response(resp)


@login_required
# #@timeit
def get_label_problem_lists(request, patient_id, user_id):
    resp = {'success': False}

    user = User.objects.get(id=user_id)

    if user.profile.role == 'nurse' or user.profile.role == 'secretary':
        team_members = PhysicianTeam.objects.filter(member=user)
        if team_members:
            user = team_members[0].physician

    lists = LabeledProblemList.objects.filter(user=user, patient_id=patient_id)
    lists_holder = []
    # TODO: To verify the updated logic
    for label_list in lists:
        problem_list = label_list.problem_list
        if problem_list:
            problems_qs = Problem.objects.filter(labels__in=label_list.labels.all()).filter(is_active=True).distinct()
            problems = []
            for problem in problems_qs:
                if problem.id in problem_list:
                    problems.insert(0, problem)
                else:
                    problems.append(problem)
        else:
            problems = Problem.objects.filter(labels__in=label_list.labels.all()).filter(
                is_active=True).distinct().order_by('start_date')

        problems_holder = ProblemSerializer(problems, many=True).data
        if not label_list.problem_list:
            ProblemService.populate_multiplicity(problems_holder)
            problems_holder = sorted(problems_holder, key=operator.itemgetter('multiply'), reverse=True)

        list_dict = LabeledProblemListSerializer(label_list).data
        list_dict['problems'] = problems_holder
        lists_holder.append(list_dict)

    resp = {
        'problem_lists': lists_holder
    }
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def delete_problem_list(request, list_id):
    resp = {'success': False}

    LabeledProblemList.objects.get(id=list_id).delete()
    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def rename_problem_list(request, list_id):
    resp = {'success': False}

    name = request.POST.get('name')
    LabeledProblemList.objects.filter(id=list_id).update(name=name)

    resp = {'success': True}
    return ajax_response(resp)


@login_required
#@timeit
def get_problems(request, patient_id):
    resp = {'success': False}

    problems = Problem.objects.filter(patient_id=patient_id)

    resp = {
        "problems": ProblemSerializer(problems, many=True).data
    }
    return ajax_response(resp)


@login_required
#@timeit
def get_sharing_problems(request, patient_id, sharing_patient_id):
    resp = {'success': False}

    sharing = SharingPatient.objects.get(shared_id=patient_id, sharing_id=sharing_patient_id)

    resp = {
        'sharing_problems': ProblemSerializer(sharing.problems.all(), many=True).data,
        'is_my_story_shared': sharing.is_my_story_shared
    }
    return ajax_response(resp)


@login_required
#@timeit
def remove_sharing_problems(request, patient_id, sharing_patient_id, problem_id):
    resp = {'success': False}

    sharing_patient = SharingPatient.objects.get(shared_id=patient_id, sharing_id=sharing_patient_id)
    problem = Problem.objects.get(id=problem_id)
    sharing_patient.problems.remove(problem)

    actor_profile = UserProfile.objects.get(user=request.user)
    activity = "Removed access for patient <b>%s</b> " % sharing_patient.sharing.username
    add_problem_activity(problem, request.user, activity)

    resp = {'success': True}
    return ajax_response(resp)


@login_required
#@timeit
def add_sharing_problems(request, patient_id, sharing_patient_id, problem_id):
    resp = {'success': False}

    sharing_patient = SharingPatient.objects.get(shared_id=patient_id, sharing_id=sharing_patient_id)
    problem = Problem.objects.get(id=problem_id)
    sharing_patient.problems.add(problem)

    actor_profile = UserProfile.objects.get(user=request.user)
    activity = "Added access for patient <b>%s</b> " % sharing_patient.sharing.username
    add_problem_activity(problem, request.user, activity)

    resp = {'success': True}
    return ajax_response(resp)


@permissions_required(["add_problem_label"])
@login_required
#@timeit
def update_problem_list_note(request, list_id):
    resp = {'success': False}
    problem_list = LabeledProblemList.objects.get(id=list_id)
    problem_list.note = request.POST.get('note')
    problem_list.save()

    activity = '"%s" was added to the folder "%s"' % (problem_list.note, problem_list.name)
    physician = request.user
    patient = problem_list.patient
    op_add_event(physician, patient, activity)

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_common_problem_list"])
@login_required
#@timeit
def add_new_common_problem(request, staff_id):
    resp = {'success': False}
    problem_name = request.POST.get('problem_name')
    concept_id = request.POST.get('concept_id', None)
    problem_type = request.POST.get('problem_type', None)

    if CommonProblem.objects.filter(concept_id=concept_id, author=request.user).exists():
        resp['msg'] = 'Problem already added'
        return ajax_response(resp)

    problem = CommonProblem(problem_name=problem_name, concept_id=concept_id, author=request.user,
                            problem_type=problem_type)
    problem.save()

    common_problem = CommonProblemSerializer(problem).data
    resp['common_problem'] = common_problem
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_common_problem_list"])
@login_required
#@timeit
def get_common_problems(request, staff_id):
    resp = {'success': False}

    problems = CommonProblem.objects.filter(author=request.user).order_by('problem_name')
    common_problems = CommonProblemSerializer(problems, many=True).data
    resp['problems'] = common_problems
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_common_problem_list"])
@login_required
#@timeit
def remove_common_problem(request, problem_id):
    resp = {'success': False}
    problem = CommonProblem.objects.get(id=problem_id)
    if problem.author == request.user:
        problem.delete()
        resp['success'] = True

    return ajax_response(resp)


@login_required
#@timeit
def get_data_pins(request, problem_id):
    resp = {'success': False}

    pins = ObservationPinToProblem.objects.filter(problem_id=problem_id)
    observations = [x.observation for x in pins]

    resp['success'] = True
    resp['pins'] = ObservationSerializer(observations, many=True).data
    resp['problem_pins'] = ObservationPinToProblemSerializer(pins, many=True).data
    return ajax_response(resp)


@login_required
#@timeit
def get_medication_pins(request, problem_id):
    resp = {}
    pins = MedicationPinToProblem.objects.filter(problem_id=problem_id)
    resp['success'] = True
    resp['pins'] = MedicationPinToProblemSerializer(pins, many=True).data
    return ajax_response(resp)


@permissions_required(["delete_problem"])
@login_required
#@timeit
def delete_problem(request, problem_id):
    resp = {'success': False}

    physician = request.user
    patient_id = request.POST.get('patient_id', None)
    latest_encounter = Encounter.objects.filter(physician=physician,
                                                patient_id=patient_id
                                                ).order_by('-starttime').first()

    if latest_encounter and latest_encounter.stoptime is None:
        resp['success'] = True

        problem = Problem.objects.get(id=problem_id)
        summary = "Deleted <u>problem</u>: <b>%s</b>" % problem.problem_name
        op_add_event(physician, problem.patient, summary)
        problem.delete()

    return ajax_response(resp)


@login_required
#@timeit
def get_related_encounters(request, problem_id):
    resp = {'success': False}
    problem = get_object_or_404(Problem, pk=problem_id)
    encounter_records = problem.problem_encounter_records
    related_encounters = [record.encounter for record in encounter_records.all()]

    resp['encounters'] = EncounterSerializer(related_encounters, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def get_related_documents(request, problem_id):
    """
    Get document pinned to problem direct or via todo 
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    # Loading problem info
    problem_info = Problem.objects.prefetch_related(
        Prefetch("todo_set", queryset=ToDo.objects.order_by("order"))
    ).get(id=problem_id)

    # Loading document pinned directly to problem
    problem_document_set = problem_info.document_set.all()

    problem_todo_document_set = []
    problem_todo_set = problem_info.todo_set.all()
    for problem_todo in problem_todo_set:
        if problem_todo.document_set.count() != 0:
            problem_todo_document_set += problem_todo.document_set.all()

    document_result_set = set(list(problem_document_set) + list(problem_todo_document_set))

    # Need remove duplicated and sorted by creation date
    resp['documents'] = DocumentSerializer(document_result_set, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def get_problem_todos(request, problem_id):
    """
    Loading all todo which have been pinned to the problem and
    todos which have medication pinned to this problem also
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}
    is_accomplished = request.GET.get('accomplished') == 'true'
    page = int(request.GET.get('page', 1))
    load_all = request.GET.get('all', 'false') == 'true'
    per_page = 5

    todo = ToDo.objects.filter(accomplished=is_accomplished).filter(
        Q(problem_id=problem_id) | Q(medication__medication_pin_medications__problem_id=problem_id))
    if not load_all:
        todo = todo[per_page * (page - 1):per_page * page]

    resp['data'] = ProblemTodoSerializer(todo, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
#@timeit
def get_problem_goals(request, problem_id):
    """
    Loading all problem's goals
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    problem_info = get_object_or_404(Problem, pk=problem_id)

    resp['goals'] = GoalSerializer(problem_info.goal_set, many=True).data
    resp['success'] = True
    return ajax_response(resp)


@login_required
# @deprecated
#@timeit
def get_problem_wikis(request, problem_id):
    """
    Loading all problem's history notes
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    history_note = ProblemNote.objects.filter(note_type='history', problem_id=problem_id).order_by(
        '-created_on').first()

    problem_notes = {
        'history': ProblemNoteSerializer(history_note).data
    }

    resp['history_note'] = problem_notes['history']
    resp['history_note_total'] = ProblemNote.objects.filter(note_type='history', problem_id=problem_id).count()
    resp['success'] = True

    return ajax_response(resp)


@login_required
#@timeit
def get_problem_images(request, problem_id):
    """
    Loading all problem's images
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}
    problem_images = PatientImage.objects.filter(problem_id=problem_id)

    resp['images'] = PatientImageSerializer(problem_images, many=True).data
    resp['success'] = True

    return ajax_response(resp)


@login_required
#@timeit
def get_problem_relationships(request, problem_id):
    """
    Loading problem's relationships
    :param request:
    :param problem_id:
    :return:
    """
    resp = {'success': False}
    problem_info = Problem.objects.get(id=problem_id)

    effecting_relations = ProblemRelationship.objects.filter(target_id=problem_id)
    effecting_problems = [relationship.source.id for relationship in effecting_relations]

    effected_relations = ProblemRelationship.objects.filter(source_id=problem_id)
    effected_problems = [relationship.target.id for relationship in effected_relations]

    patient_problems = Problem.objects.filter(patient=problem_info.patient).exclude(id=problem_id)

    resp['effecting_problems'] = effecting_problems
    resp['effected_problems'] = effected_problems
    resp['patient_problems'] = ProblemSerializer(patient_problems, many=True).data
    resp['success'] = True

    return ajax_response(resp)


@login_required
#@timeit
def problem_notes_function(request, problem_id):
    """

    :param request:
    :param problem_id:
    :return:
    """
    # TODO: Add a new problem's note (either wiki or history)
    resp = {'success': False}
    if request.method == "POST":
        responseBody = json.loads(request.body)

        actor = request.user
        actor_profile = UserProfile.objects.get(user=actor)
        note = responseBody.get('note')  # <- TODO: Sanitize to prevent SQL Injection Attack
        note_type = responseBody.get('note_type')  # <- TODO: Validate note type
        # physician = request.user

        #  Validation
        try:
            problem = Problem.objects.get(id=problem_id)
            # author_profile = UserProfile.objects.get(user=request.user)
        except (Problem.DoesNotExist, UserProfile.DoesNotExist):
            return ajax_response(resp)

        #  Adding new note
        new_note = ProblemNote.objects.create_problem_note(actor, problem, note, note_type)

        # Save problem activity
        activity = 'Added wiki note: <b>%s</b>' % note
        add_problem_activity(problem, request.user, activity, 'input')

        # Add operation event
        op_add_event(actor, problem.patient, activity, problem)

        # Auto generate to do correspond to note https://trello.com/c/hkdbHZjw
        auto_generate_note_todo(actor_profile, problem.patient, problem, request, resp)

        resp['note'] = ProblemNoteSerializer(new_note).data
        resp['success'] = True
    if request.method == "GET":
        note_type = request.GET.get('type')  # this is required
        before = request.GET.get('before', 1000000000)  # this is optional
        limit = int(request.GET.get('limit', 10))

        # TODO: Getting list of notes with default reserve chronology (most recent on top)
        notes = ProblemNote.objects.filter(problem_id=problem_id, note_type=note_type, id__lt=before).order_by(
            '-created_on')[0:limit]

        resp['notes'] = ProblemNoteSerializer(notes.all(), many=True).data
        resp['total'] = ProblemNote.objects.filter(problem_id=problem_id, note_type=note_type, id__lt=before).count()
        resp['success'] = True
    if request.method == "DELETE":
        pass
    return ajax_response(resp)
