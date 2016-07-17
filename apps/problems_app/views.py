#!/usr/bin/env python
try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps

import json
import operator
from datetime import datetime, timedelta
from django.db.models import Max
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from common.views import *

from emr.models import UserProfile, Problem, ProblemOrder, ProblemLabel, LabeledProblemList
from emr.models import Goal, ToDo, TextNote, PatientImage
from emr.models import ProblemRelationship
from emr.models import ProblemNote, ProblemActivity, ProblemSegment, CommonProblem
from emr.models import EncounterProblemRecord, Encounter
from emr.models import Observation, SharingPatient, PhysicianTeam, ObservationComponent

from emr.operations import op_add_event, op_add_todo_event


from .serializers import ProblemSerializer, PatientImageSerializer, ProblemLabelSerializer, LabeledProblemListSerializer, ProblemInfoSerializer
from .serializers import ProblemNoteSerializer, ProblemActivitySerializer, CommonProblemSerializer
from emr.serializers import TextNoteSerializer
from todo_app.serializers import TodoSerializer
from goals_app.serializers import GoalSerializer
from encounters_app.serializers import EncounterSerializer
from users_app.serializers import UserProfileSerializer

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity
from todo_app.operations import add_todo_activity
from observations_app.serializers import ObservationSerializer


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


@login_required
def track_problem_click(request, problem_id):
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    if actor_profile.role in ['physician', 'admin']:
        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        summary = "Clicked <u>problem</u>: <b>%s</b>" % problem.problem_name
        op_add_event(actor, patient, summary)

        activity = "Visited <u>problem</u>: <b>%s</b>" % problem.problem_name
        add_problem_activity(problem, actor_profile, activity)

    resp = {}
    return ajax_response(resp)


# Problem
@login_required
def get_problem_info(request, problem_id):
    problem_info = Problem.objects.select_related("patient").prefetch_related(
                                "goal_set",
                                "patientimage_set",
                                "target", "source",
                                "problemactivity_set",
                                "problem_encounter_records",
                                "problem_observations",
                                Prefetch("todo_set", queryset=ToDo.objects.order_by("order"))
                        ).get(id=problem_id)

    # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
    if problem_info.concept_id in ['73211009', '46635009', '44054006']:
        Observation.objects.create_if_not_exist(problem_info)

    serialized_problem = ProblemInfoSerializer(problem_info).data
    # Notes - Todo
    patient_notes = []
    physician_notes = []
    patient_note_holder = [TextNoteSerializer(note).data for note in patient_notes]
    physician_note_holder = [TextNoteSerializer(note).data for note in physician_notes]

    sharing_patients = SharingPatient.objects.select_related("problems").filter(
                            shared=problem_info.patient).order_by('sharing__first_name', 'sharing__last_name')

    sharing_patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        user_dict['problems'] = [x.id for x in sharing_patient.problems.all()]
        sharing_patients_list.append(user_dict)

    resp = {
        'success': True,
        'info': serialized_problem,
        'patient_notes': patient_note_holder,
        'physician_notes': physician_note_holder,
        'problem_goals': serialized_problem["problem_goals"],
        'problem_todos': serialized_problem["problem_todos"],
        'problem_images': serialized_problem["problem_images"],
        'effecting_problems': serialized_problem["effecting_problems"],
        'effected_problems': serialized_problem["effected_problems"],
        'patient_problems': serialized_problem["patient_other_problems"],
        'history_note': serialized_problem["problem_notes"]["history"],
        'wiki_notes': serialized_problem["problem_notes"]["wiki_notes"],
        'activities': serialized_problem["activities"],
        'related_encounters': serialized_problem["related_encounters"],
        'observations': serialized_problem["observations"],
        'sharing_patients': sharing_patients_list
    }

    return ajax_response(resp)


@login_required
def get_observations(request, problem_id):
    observations = Observation.objects.filter(problem__id=problem_id)
    serialized_observations = ObservationSerializer(observations, many=True).data
    resp = {}
    resp['success'] = True
    resp['observations'] = serialized_observations
    return ajax_response(resp)

@login_required
def get_problem_activity(request, problem_id, last_id):
    problem = get_object_or_404(Problem, pk=problem_id)
    activities = ProblemActivity.objects.filter(problem=problem).filter(id__gt=last_id)
    activity_holder = ProblemActivitySerializer(activities, many=True).data
    resp = {}
    resp['activities'] = activity_holder
    resp['success'] = True
    return ajax_response(resp)


# Problem
@login_required
def add_patient_problem(request, patient_id):
    resp = {}
    resp['success'] = False

    actor_profile, permitted = check_permissions(['add_problem'], request.user)
    if not permitted or request.method == "GET":
        return ajax_response(resp)

    term = request.POST.get('term')
    concept_id = request.POST.get('code', None)
    if Problem.objects.filter(problem_name=term, patient__id=patient_id).exists():
        resp['msg'] = 'Problem already added'
        return ajax_response(resp)

    new_problem = Problem.objects.create_new_problem(patient_id, term, concept_id, actor_profile)
    physician = request.user

    summary = 'Added <u>problem</u> <b>%s</b>' % term
    op_add_event(physician, new_problem.patient, summary, new_problem)
    activity = "Added <u>problem</u>: <b>%s</b>" % term
    add_problem_activity(new_problem, actor_profile, activity)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(new_problem).data
    return ajax_response(resp)


@login_required
def add_patient_common_problem(request, patient_id):
    resp = {}
    resp['success'] = False

    actor_profile, permitted = check_permissions(['add_problem'], request.user)
    if not permitted or request.method == "GET":
        return ajax_response(resp)

    cproblem = request.POST.get('cproblem')
    problem_type = request.POST.get('type')

    problem = CommonProblem.objects.get(id=cproblem)

    if Problem.objects.filter(problem_name=problem.problem_name, concept_id=problem.concept_id, patient__id=patient_id).exists():
        resp['msg'] = 'Problem already added'
        return ajax_response(resp)

    new_problem = Problem.objects.create_new_problem(patient_id, problem.problem_name, problem.concept_id, actor_profile)
    physician = request.user

    summary = 'Added <u>problem</u> <b>%s</b>' % problem.problem_name
    op_add_event(physician, new_problem.patient, summary, new_problem)
    activity = "Added <u>problem</u>: <b>%s</b>" % problem.problem_name
    add_problem_activity(new_problem, actor_profile, activity)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(new_problem).data
    return ajax_response(resp)


@login_required
def change_name(request, problem_id):
    resp = {}
    resp['success'] = False

    actor_profile, permitted = check_permissions(['change_problem_name'], request.user)
    if not permitted or request.method == "GET":
        return ajax_response(resp)

    term = request.POST.get('term')
    concept_id = request.POST.get('code', None)

    problem = Problem.objects.get(id=problem_id)
    if Problem.objects.filter(problem_name=term, patient=problem.patient).exists():
        resp['msg'] = 'Problem already added'
        return ajax_response(resp)

    old_problem_concept_id = problem.concept_id
    old_problem_name = problem.problem_name
    if datetime.now() > datetime.strptime(problem.start_date.strftime('%d/%m/%Y') + ' ' + problem.start_time.strftime('%H:%M:%S'), "%d/%m/%Y %H:%M:%S") + timedelta(hours=24):
        problem.old_problem_name = old_problem_name

    problem.problem_name = term
    problem.concept_id = concept_id
    problem.save()

    physician = request.user

    if old_problem_concept_id and problem.concept_id:
        summary = '<b>%s (%s)</b> was changed to <b>%s (%s)</b>' % (old_problem_name, old_problem_concept_id, problem.problem_name, problem.concept_id)
    elif old_problem_concept_id:
        summary = '<b>%s (%s)</b> was changed to <b>%s</b>' % (old_problem_name, old_problem_concept_id, problem.problem_name)
    elif problem.concept_id:
        summary = '<b>%s</b> was changed to <b>%s (%s)</b>' % (old_problem_name, problem.problem_name, problem.concept_id)
    else:
        summary = '<b>%s</b> was changed to <b>%s</b>' % (old_problem_name, problem.problem_name)

    op_add_event(physician, problem.patient, summary, problem)
    add_problem_activity(problem, actor_profile, summary)

    resp['success'] = True
    resp['problem'] = ProblemSerializer(problem).data

    # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
    # if concept_id in ['73211009', '46635009', '44054006']:
    #     observation = Observation()
    #     observation.problem = problem
    #     observation.subject = problem.patient.profile
    #     observation.save()

    return ajax_response(resp)

# Problems
@login_required
def update_problem_status(request, problem_id):
    # Different permissions for different cases
    # Modify this view

    resp = {}
    resp['success'] = False

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
    add_problem_activity(problem, actor_profile, activity)

    resp['success'] = True
    return ajax_response(resp)


# Problems
@login_required
def update_start_date(request, problem_id):
    resp = {}
    resp['success'] = False

    actor_profile, permitted = check_permissions(['modify_problem'], request.user)
    if not permitted:
        return ajax_response(resp)

    start_date = request.POST.get('start_date')
    problem = Problem.objects.get(id=problem_id)
    problem.start_date = get_new_date(start_date)
    problem.save()

    physician = request.user
    patient = problem.patient
    summary = '''Changed <u>problem</u> : <b>%s</b> start date to <b>%s</b>''' % (problem.problem_name, problem.start_date)
    op_add_event(physician, patient, summary, problem)
    activity = summary
    add_problem_activity(problem, actor_profile, activity)

    resp['success'] = True
    return ajax_response(resp)


# Add History Note
@login_required
def add_history_note(request, problem_id):
    resp = {}
    resp['success'] = False

    permissions = ['modify_problem']
    actor_profile, permitted = check_permissions(permissions, request.user)
    if not permitted or request.method == "GET":
        return ajax_response(resp)

    note = request.POST.get('note')
    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        return ajax_response(resp)

    new_note = ProblemNote.objects.create_history_note(actor_profile, problem, note)

    activity = 'Added History Note  <b>%s</b>' % note
    add_problem_activity(problem, actor_profile, activity, 'input')

    physician = request.user
    patient = problem.patient
    op_add_event(physician, patient, activity, problem)

    resp['success'] = True
    resp['note'] = ProblemNoteSerializer(new_note).data
    return ajax_response(resp)


# Add Wiki Note
@login_required
def add_wiki_note(request, problem_id):
    resp = {}
    resp['success'] = False

    # Check if user is able to view patient
    # Todo
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    if request.method == 'POST':
        note = request.POST.get('note')
        try:
            problem = Problem.objects.get(id=problem_id)
            author = UserProfile.objects.get(user=request.user)
        except (Problem.DoesNotExist, UserProfile.DoesNotExist) as e:
            return ajax_response(resp)

        new_note = ProblemNote.objects.create_wiki_note(author, problem, note)

        activity = 'Added wiki note: <b>%s</b>' % note
        add_problem_activity(problem, actor_profile, activity, 'input')

        physician = request.user
        patient = problem.patient
        op_add_event(physician, patient, activity, problem)

        resp['note'] = ProblemNoteSerializer(new_note).data
        resp['success'] = True

    return ajax_response(resp)


# Problems
@login_required
def add_patient_note(request, problem_id):

    resp = {}

    resp['success'] = False
    errors = []

    problem = Problem.objects.get(id=problem_id)
    patient = problem.patient
    patient_profile = UserProfile.objects.get(user=patient)

    note = request.POST.get('note')

    if request.user == patient:
        new_note = TextNote(
            author=patient_profile, by='patient', note=note)
        new_note.save()

        problem.notes.add(new_note)

        activity = 'Added patient note'
        add_problem_activity(problem, patient_profile, activity, 'input')

        new_note_dict = TextNoteSerializer(new_note).data
        resp['success'] = True
        resp['note'] = new_note_dict
    else:
        errors.append("Permission Error: Only patient can add patient note.")

    resp['errors'] = errors
    return ajax_response(resp)


# Problems
@login_required
def add_physician_note(request, problem_id):

    # More work required

    resp = {}
    resp['success'] = False

    problem = Problem.objects.get(id=problem_id)
    patient = problem.patient
    note = request.POST.get('note')

    physician = request.user

    physician_profile = UserProfile.objects.get(user=physician)

    new_note = TextNote(
        author=physician_profile, by='physician', note=note)
    new_note.save()

    problem.notes.add(new_note)

    summary = '''Added <u>note</u> : <b>%s</b> to <u>problem</u> : <b>%s</b>''' % (note, problem.problem_name)
    op_add_event(physician, patient, summary, problem)

    activity = summary
    add_problem_activity(problem, physician_profile, activity, 'input')

    new_note_dict = TextNoteSerializer(new_note).data
    resp['note'] = new_note_dict
    resp['success'] = True
    return ajax_response(resp)


# Problems
@login_required
def add_problem_goal(request, problem_id):

    resp = {}

    resp['success'] = False

    permissions = ['add_goal']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        goal = request.POST.get('name')

        new_goal = Goal(
            patient=patient, problem=problem, goal=goal)

        new_goal.save()

        physician = request.user

        summary = '''Added <u> goal </u> : <b>%s</b> to <u>problem</u> : <b>%s</b>''' % (goal, problem.problem_name)
        op_add_event(physician, patient, summary, problem)

        activity = summary
        add_problem_activity(problem, actor_profile, activity, 'output')
        new_goal_dict = GoalSerializer(new_goal).data
        resp['success'] = True
        resp['goal'] = new_goal_dict
    return ajax_response(resp)


# Problems
@login_required
def add_problem_todo(request, problem_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        problem = Problem.objects.get(id=problem_id)

        # set problem authentication to false if not physician, admin
        actor_profile = UserProfile.objects.get(user=request.user)

        role = actor_profile.role

        if role in ['physician', 'admin']:
            authenticated = True
        else:
            authenticated = False

        problem.authenticated = authenticated
        problem.save()

        patient = problem.patient

        todo = request.POST.get('name')
        due_date = request.POST.get('due_date', None)
        if due_date:
            due_date = datetime.strptime(due_date, '%m/%d/%Y').date()

        new_todo = ToDo(
            patient=patient, problem=problem, todo=todo, due_date=due_date)

        observation_id = request.POST.get('observation_id', None)
        if observation_id:
            observation = Observation.objects.get(id=int(observation_id))
            new_todo.observation = observation

            todo_past_six_months = request.POST.get('todo_past_six_months', None)
            if todo_past_six_months:
                observation.todo_past_six_months = True
                observation.save()

        order =  ToDo.objects.all().aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        new_todo.order = order
        new_todo.save()

        physician = request.user

        summary = '''Added <u>todo</u> : <a href="#/todo/%s"><b>%s</b></a> to <u>problem</u> : <b>%s</b>''' % (new_todo.id, todo, problem.problem_name)
        op_add_event(physician, patient, summary, problem)

        activity = summary
        add_problem_activity(problem, actor_profile, activity, 'output')

        summary = '''Added <u>todo</u> <a href="#/todo/%s"><b>%s</b></a> for <u>problem</u> <b>%s</b>''' % (new_todo.id, new_todo.todo, problem.problem_name)

        op_add_todo_event(physician, patient, summary, new_todo, True)
        # todo activity
        activity = '''
            Added this todo.
        '''
        add_todo_activity(new_todo, actor_profile, activity)

        new_todo_dict = TodoSerializer(new_todo).data

        resp['success'] = True
        resp['todo'] = new_todo_dict

    return ajax_response(resp)


# Problems
@login_required
def upload_problem_image(request, problem_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_problem_image']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:

        actor = request.user
        actor_profile = UserProfile.objects.get(user=actor)

        role = actor_profile.role

        if role in ['physician', 'admin']:
            authenticated = True
        else:
            authenticated = False

        problem = Problem.objects.get(id=problem_id)
        problem.authenticated = authenticated
        problem.save()

        patient = problem.patient

        images = request.FILES.getlist('file[]')
        for image in images:
            patient_image = PatientImage(
                patient=patient,
                problem=problem,
                image=image)

            patient_image.save()

            filename = str(patient_image.image.path)
            img = Image.open(filename)

            if img.mode not in ('L', 'RGB'):
                img = img.convert('RGB')

            img.thumbnail((160,160), Image.ANTIALIAS)
            img.save(filename)

            summary = '''Physician added <u>image</u> to <u>problem</u> <b>%s</b> <br/><a href="/media/%s"><img src="/media/%s" class="thumbnail thumbnail-custom" /></a>''' % (problem.problem_name, patient_image.image, patient_image.image)

            op_add_event(actor, patient, summary, problem)

            activity = summary
            add_problem_activity(problem, actor_profile, activity, 'input')

            resp['success'] = True

    return ajax_response(resp)


# Problems
@login_required
def delete_problem_image(request, problem_id, image_id):
    resp = {}
    resp['success'] = False

    permissions = ['delete_problem_image']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:
        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        image = PatientImage.objects.get(id=image_id)
        image.delete()

        physician = request.user
        summary = '''Deleted <u>image</u> from <u>problem</u> : <b>%s</b>''' % problem.problem_name
        op_add_event(physician, patient, summary, problem)

        activity = summary
        add_problem_activity(problem, actor_profile, activity, 'input')

        resp['success'] = True

    return ajax_response(resp)


@login_required
def relate_problem(request):

    resp = {}
    resp['success'] = False

    permissions = ['relate_problem']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:
        relationship = request.POST.get('relationship') == 'true'
        source_id = request.POST.get('source_id', None)
        target_id = request.POST.get('target_id', None)

        source = Problem.objects.get(id=source_id)
        target = Problem.objects.get(id=target_id)

        if relationship:
            try:
                problem_relationship = ProblemRelationship.objects.get(
                    source=source, target=target)
            except ProblemRelationship.DoesNotExist:
                problem_relationship = ProblemRelationship.objects.create(
                    source=source, target=target)
                activity = '''Created Problem Relationship: <b>%s</b> effects <b>%s</b>''' % (source.problem_name, target.problem_name)

                add_problem_activity(source, actor_profile, activity)
                add_problem_activity(target, actor_profile, activity)

                op_add_event(request.user, source.patient, activity)
        else:

            problem_relationship = ProblemRelationship.objects.get(
                source=source, target=target)

            problem_relationship.delete()

            activity = '''Removed Problem Relationship: <b>%s</b> effects <b>%s</b>''' % (source.problem_name, target.problem_name)

            add_problem_activity(source, actor_profile, activity)
            add_problem_activity(target, actor_profile, activity)

            op_add_event(request.user, source.patient, activity)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def update_by_ptw(request):

    resp = {}

    resp['success'] = False

    permissions = ['modify_problem']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        timeline_data = json.loads(request.body)['timeline_data']
        for problem_json in timeline_data['problems']:
            problem = Problem.objects.get(id=int(problem_json['id']))
            patient = problem.patient

            start_date = problem_json['events'][-1]['startTime']
            problem.start_date = datetime.strptime(start_date, "%d/%m/%Y %H:%M:%S").date()
            problem.start_time = datetime.strptime(start_date, "%d/%m/%Y %H:%M:%S").time()

            role = actor_profile.role

            if role in ['physician', 'admin']:
                authenticated = True
            else:
                authenticated = False
            problem.authenticated = authenticated

            problem.save()

            if len(problem_json['events']) > 1:
                i = 1
                for event in problem_json['events']:
                    # break if the last one, this is current problem
                    if i == len(problem_json['events']):
                        break
                    i = i + 1
                    try:
                        event_id = int(event['event_id'])
                        try:
                            problem_segment = ProblemSegment.objects.get(event_id=event_id)
                        except ProblemSegment.DoesNotExist:
                            problem_segment = ProblemSegment()
                            problem_segment.event_id = event_id
                            problem_segment.problem = problem

                        problem_segment.start_date = datetime.strptime(event['startTime'], "%d/%m/%Y %H:%M:%S").date()
                        problem_segment.start_time = datetime.strptime(event['startTime'], "%d/%m/%Y %H:%M:%S").time()
                        if event['state'] == 'uncontrolled':
                            problem_segment.is_active = True
                            problem_segment.is_controlled = False
                        if event['state'] == 'controlled':
                            problem_segment.is_active = True
                            problem_segment.is_controlled = True
                        if event['state'] == 'inactive':
                            problem_segment.is_active = False
                            problem_segment.is_controlled = False
                        problem_segment.save()
                    except ValueError:
                        event_id = None

            physician = request.user

            summary = '''Changed <u>problem</u> :<b>%s</b> start date to <b>%s</b>''' % (problem.problem_name, problem.start_date)
            op_add_event(physician, patient, summary, problem)

            activity = summary
            add_problem_activity(problem, actor_profile, activity)

            resp['success'] = True

    return ajax_response(resp)

@login_required
def update_state_to_ptw(request):

    resp = {}

    resp['success'] = False

    permissions = ['modify_problem']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        timeline_data = json.loads(request.body)['timeline_data']
        for problem_json in timeline_data['problems']:
            problem = Problem.objects.get(id=int(problem_json['id']))

            start_date = problem_json['events'][-1]['startTime']
            problem.start_date = datetime.strptime(start_date, "%d/%m/%Y %H:%M:%S").date()
            problem.start_time = datetime.strptime(start_date, "%d/%m/%Y %H:%M:%S").time()
            problem.save()

            if len(problem_json['events']) > 1:
                i = 1
                for event in problem_json['events']:
                    # break if the last one, this is current problem
                    if i == len(problem_json['events']):
                        break
                    i = i + 1
                    try:
                        event_id = int(event['event_id'])
                        try:
                            problem_segment = ProblemSegment.objects.get(event_id=event_id)
                        except ProblemSegment.DoesNotExist:
                            problem_segment = ProblemSegment()
                            problem_segment.event_id = event_id
                            problem_segment.problem = problem

                        problem_segment.start_date = datetime.strptime(event['startTime'], "%d/%m/%Y %H:%M:%S").date()
                        problem_segment.start_time = datetime.strptime(event['startTime'], "%d/%m/%Y %H:%M:%S").time()
                        if event['state'] == 'uncontrolled':
                            problem_segment.is_active = True
                            problem_segment.is_controlled = False
                        if event['state'] == 'controlled':
                            problem_segment.is_active = True
                            problem_segment.is_controlled = True
                        if event['state'] == 'inactive':
                            problem_segment.is_active = False
                            problem_segment.is_controlled = False
                        problem_segment.save()
                    except ValueError:
                        event_id = None

            resp['success'] = True

    return ajax_response(resp)

@login_required
def update_order(request):
    resp = {}

    resp['success'] = False

    permissions = ['set_problem_order']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        datas = json.loads(request.body)
        if datas.has_key('patient_id'):
            id_problems = datas['problems']
            patient_id = datas['patient_id']
            patient = User.objects.get(id=int(patient_id))

            try:
                problem = ProblemOrder.objects.get(user=request.user, patient=patient)
            except ProblemOrder.DoesNotExist:
                problem = ProblemOrder(user=request.user, patient=patient)
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

@login_required
def new_problem_label(request, problem_id):
    resp = {}
    resp['success'] = False
    resp['status'] = False
    resp['new_status'] = False

    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        name = request.POST.get('name')
        css_class = request.POST.get('css_class')

        problem = Problem.objects.get(id=problem_id)
        label = ProblemLabel.objects.filter(name=name, css_class=css_class, author=request.user, patient=problem.patient)
        if not label:
            label = ProblemLabel(name=name, css_class=css_class, author=request.user, patient=problem.patient)
            label.save()
            resp['new_status'] = True
            resp['new_label'] = ProblemLabelSerializer(label).data
        else:
            label = label[0]

        if not label in problem.labels.all():
            problem.labels.add(label)
            resp['status'] = True
            resp['label'] = ProblemLabelSerializer(label).data

        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_problem_labels(request, patient_id, user_id):

    user = User.objects.get(id=user_id)
    patient = User.objects.get(id=patient_id)
    labels = ProblemLabel.objects.filter(patient=patient, author=user)

    labels_holder = []
    for label in labels:
        label_dict = ProblemLabelSerializer(label).data
        labels_holder.append(label_dict)

    resp = {}
    resp['labels'] = labels_holder

    return ajax_response(resp)

@login_required
def save_edit_problem_label(request, label_id, patient_id, user_id):
    resp = {}
    resp['success'] = False
    resp['status'] = False

    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        name = request.POST.get('name')
        css_class = request.POST.get('css_class')

        label = ProblemLabel.objects.get(id=label_id)
        user = User.objects.get(id=user_id)
        patient = User.objects.get(id=patient_id)

        if not ProblemLabel.objects.filter(name=name, css_class=css_class, patient=patient, author=user):
            label.name = name
            label.css_class = css_class
            label.save()
            resp['status'] = True

        resp['label'] = ProblemLabelSerializer(label).data

        resp['success'] = True

    return ajax_response(resp)

@login_required
def add_problem_label(request, label_id, problem_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        problem = Problem.objects.get(id=problem_id)

        label = ProblemLabel.objects.get(id=label_id)
        problem.labels.add(label)

        resp['success'] = True

    return ajax_response(resp)


@login_required
def remove_problem_label(request, label_id, problem_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        problem = Problem.objects.get(id=problem_id)
        label = ProblemLabel.objects.get(id=label_id)
        problem.labels.remove(label)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_problem_label(request, label_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        label = ProblemLabel.objects.get(id=label_id)
        label.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def add_problem_list(request, patient_id, user_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        datas = json.loads(request.body)
        list_name = datas['name']
        labels = datas['labels']
        user = User.objects.get(id=user_id)
        patient = User.objects.get(id=patient_id)

        new_list = LabeledProblemList(user=user, name=list_name, patient=patient)
        new_list.save()

        label_ids = []
        for label in labels:
            l = ProblemLabel.objects.get(id=label['id'])
            new_list.labels.add(l)
            label_ids.append(l.id)


        new_list_dict = LabeledProblemListSerializer(new_list).data

        problems = Problem.objects.filter(labels__id__in=label_ids).distinct().order_by('start_date')
        problems_holder = []
        for problem in problems:
            problem_dict = ProblemSerializer(problem).data
            problems_holder.append(problem_dict)

        for problem in problems_holder:
            todo = ToDo.objects.filter(problem__id=problem['id'], accomplished=False).count()
            event = ProblemActivity.objects.filter(problem__id=problem['id'], created_on__gte=datetime.now()-timedelta(days=30)).count()
            if todo == 0 and event == 0:
                problem['multiply'] = 0
            elif todo == 0 or event == 0:
                problem['multiply'] = 1
            else:
                problem['multiply'] = todo * event

        problems_holder = sorted(problems_holder, key=operator.itemgetter('multiply'), reverse=True)


        new_list_dict['problems'] = problems_holder

        resp['new_list'] = new_list_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_label_problem_lists(request, patient_id, user_id):
    resp = {}
    patient = User.objects.get(id=patient_id)
    user = User.objects.get(id=user_id)

    if user.profile.role == 'nurse' or user.profile.role == 'secretary':
        team_members = PhysicianTeam.objects.filter(member=user)
        if team_members:
            user = team_members[0].physician

    lists = LabeledProblemList.objects.filter(user=user, patient=patient)
    lists_holder = []
    for label_list in lists:
        list_dict = LabeledProblemListSerializer(label_list).data
        label_ids = []
        for label in label_list.labels.all():
            label_ids.append(label.id)

        if label_list.problem_list:
            problems_qs = Problem.objects.filter(labels__id__in=label_ids).distinct()
            problems = []
            for id in label_list.problem_list:
                if problems_qs.filter(id=id):
                    problems.append(problems_qs.get(id=id))
            for problem in problems_qs:
                if not problem in problems:
                    problems.append(problem)

        else:
            problems = Problem.objects.filter(labels__id__in=label_ids).distinct().order_by('start_date')
        problems_holder = []
        for problem in problems:
            problem_dict = ProblemSerializer(problem).data
            problems_holder.append(problem_dict)

        if not label_list.problem_list:
            for problem in problems_holder:
                todo = ToDo.objects.filter(problem__id=problem['id'], accomplished=False).count()
                event = ProblemActivity.objects.filter(problem__id=problem['id'], created_on__gte=datetime.now()-timedelta(days=30)).count()
                if todo == 0 and event == 0:
                    problem['multiply'] = 0
                elif todo == 0 or event == 0:
                    problem['multiply'] = 1
                else:
                    problem['multiply'] = todo * event

            problems_holder = sorted(problems_holder, key=operator.itemgetter('multiply'), reverse=True)

        list_dict['problems'] = problems_holder
        lists_holder.append(list_dict)

    resp['problem_lists'] = lists_holder

    return ajax_response(resp)

@login_required
def delete_problem_list(request, list_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        problem_list = LabeledProblemList.objects.get(id=list_id)

        problem_list.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def rename_problem_list(request, list_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        problem_list = LabeledProblemList.objects.get(id=list_id)
        problem_list.name = request.POST.get('name')
        problem_list.save()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_problems(request, patient_id):
    patient = User.objects.get(id=patient_id)
    problems = Problem.objects.filter(patient=patient)

    problems_holder = ProblemSerializer(problems, many=True).data

    resp = {}
    resp['problems'] = problems_holder

    return ajax_response(resp)

@login_required
def get_sharing_problems(request, patient_id, sharing_patient_id):
    patient = User.objects.get(id=patient_id)
    sharing_patient = User.objects.get(id=sharing_patient_id)

    sharing = SharingPatient.objects.get(shared=patient, sharing=sharing_patient)

    problems_holder = ProblemSerializer(sharing.problems.all(), many=True).data

    resp = {}
    resp['sharing_problems'] = problems_holder

    return ajax_response(resp)

@login_required
def remove_sharing_problems(request, patient_id, sharing_patient_id, problem_id):
    patient = User.objects.get(id=patient_id)
    sharing_patient = User.objects.get(id=sharing_patient_id)

    sharing = SharingPatient.objects.get(shared=patient, sharing=sharing_patient)

    problem = Problem.objects.get(id=problem_id)

    sharing.problems.remove(problem)

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    activity = "Removed access for patient <b>%s</b> " % sharing_patient.username
    add_problem_activity(problem, actor_profile, activity)

    resp = {}
    resp['success'] = True

    return ajax_response(resp)

@login_required
def add_sharing_problems(request, patient_id, sharing_patient_id, problem_id):
    patient = User.objects.get(id=patient_id)
    sharing_patient = User.objects.get(id=sharing_patient_id)

    sharing = SharingPatient.objects.get(shared=patient, sharing=sharing_patient)

    problem = Problem.objects.get(id=problem_id)

    sharing.problems.add(problem)

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)
    activity = "Added access for patient <b>%s</b> " % sharing_patient.username
    add_problem_activity(problem, actor_profile, activity)

    resp = {}
    resp['success'] = True

    return ajax_response(resp)

@login_required
def update_problem_list_note(request, list_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_problem_label']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        problem_list = LabeledProblemList.objects.get(id=list_id)
        problem_list.note = request.POST.get('note')
        problem_list.save()

        activity = '"%s" was added to the folder "%s"' % (problem_list.note, problem_list.name)

        physician = request.user
        patient = problem_list.patient
        op_add_event(physician, patient, activity)

        resp['success'] = True

    return ajax_response(resp)

@login_required
def add_new_common_problem(request, staff_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_common_problem_list']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        problem_name = request.POST.get('problem_name')
        concept_id = request.POST.get('concept_id', None)
        problem_type = request.POST.get('problem_type', None)

        problem_exists = CommonProblem.objects.filter(concept_id=concept_id, author=request.user).exists()

        if problem_exists is not True:
            problem = CommonProblem(problem_name=problem_name, concept_id=concept_id, author=request.user, problem_type=problem_type)
            problem.save()

            common_problem = CommonProblemSerializer(problem).data
            resp['common_problem'] = common_problem
            resp['success'] = True

        else:
            resp['msg'] = 'Problem already added'

    return ajax_response(resp)

@login_required
def get_common_problems(request, staff_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_common_problem_list']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        problems = CommonProblem.objects.filter(author=request.user)
        common_problems = CommonProblemSerializer(problems, many=True).data
        resp['problems'] = common_problems
        resp['success'] = True

    return ajax_response(resp)

@login_required
def remove_common_problem(request, problem_id):
    resp = {}
    resp['success'] = False
    permissions = ['add_common_problem_list']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        problem = CommonProblem.objects.get(id=problem_id)
        if problem.author == request.user:
            problem.delete()
            resp['success'] = True

    return ajax_response(resp)
