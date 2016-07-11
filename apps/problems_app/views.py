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

from common.views import *

from emr.models import UserProfile, Problem, ProblemOrder, ProblemLabel, LabeledProblemList
from emr.models import Goal, ToDo, TextNote, PatientImage
from emr.models import ProblemRelationship
from emr.models import ProblemNote, ProblemActivity, ProblemSegment
from emr.models import EncounterProblemRecord, Encounter
from emr.models import Observation, SharingPatient, PhysicianTeam

from emr.operations import op_add_event, op_add_todo_event


from .serializers import ProblemSerializer, PatientImageSerializer, ProblemLabelSerializer, LabeledProblemListSerializer
from .serializers import ProblemNoteSerializer, ProblemActivitySerializer
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
    problem_info = Problem.objects.get(id=problem_id)
    # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
    if problem_info.concept_id in ['73211009', '46635009', '44054006']:
        if not Observation.objects.filter(problem=problem_info):
            observation = Observation()
            observation.problem = problem_info
            observation.subject = problem_info.patient.profile
            observation.save()

    patient = problem_info.patient

    # Notes - Todo
    patient_notes = []
    physician_notes = []

    problem_goals = Goal.objects.filter(problem=problem_info)
    problem_todos = ToDo.objects.filter(problem=problem_info).order_by('order')

    problem_images = PatientImage.objects.filter(
        problem=problem_info)

    patient_note_holder = []
    for note in patient_notes:
        note_dict = TextNoteSerializer(note).data
        patient_note_holder.append(note_dict)

    physician_note_holder = []
    for note in physician_notes:
        note_dict = TextNoteSerializer(note).data
        physician_note_holder.append(note_dict)

    problem_goals_holder = []
    for goal in problem_goals:
        goal_dict = GoalSerializer(goal).data
        problem_goals_holder.append(goal_dict)

    problem_todos_holder = []
    for todo in problem_todos:
        todo_dict = TodoSerializer(todo).data
        problem_todos_holder.append(todo_dict)

    problem_images_holder = []
    for image in problem_images:
        image_dict = PatientImageSerializer(image).data
        problem_images_holder.append(image_dict)

    history_note = ProblemNote.objects.filter(
        note_type='history', problem=problem_info).order_by(
        '-created_on').first()

    if history_note is not None:
        history_note_holder = ProblemNoteSerializer(history_note).data
    else:
        history_note_holder = None

    patient_wiki_notes = ProblemNote.objects.filter(
        note_type='wiki',
        problem=problem_info,
        author__role='patient').order_by('-created_on')

    physician_wiki_notes = ProblemNote.objects.filter(
        note_type='wiki',
        problem=problem_info,
        author__role='physician').order_by('-created_on')
    other_wiki_notes = ProblemNote.objects.filter(
        note_type='wiki', problem=problem_info).exclude(
        author__role__in=['patient', 'physician']).order_by('-created_on')

    wiki_notes_holder = {}
    wiki_notes_holder['patient'] = ProblemNoteSerializer(
        patient_wiki_notes, many=True).data
    wiki_notes_holder['physician'] = ProblemNoteSerializer(
        physician_wiki_notes, many=True).data
    wiki_notes_holder['other'] = ProblemNoteSerializer(
        other_wiki_notes, many=True).data

    problem_dict = ProblemSerializer(problem_info).data

    effecting_problems = ProblemRelationship.objects.filter(
        target=problem_info)
    effecting_problems_holder = []
    for relationship in effecting_problems:
        effecting_problems_holder.append(relationship.source.id)

    effected_problems = ProblemRelationship.objects.filter(source=problem_info)
    effected_problems_holder = []
    for relationship in effected_problems:
        effected_problems_holder.append(relationship.target.id)

    patient_problems = Problem.objects.filter(
        patient=patient).exclude(id=problem_id)
    patient_problems_holder = ProblemSerializer(
        patient_problems, many=True).data

    activites = ProblemActivity.objects.filter(problem=problem_info)
    activity_holder = ProblemActivitySerializer(activites, many=True).data

    encounter_records = EncounterProblemRecord.objects.filter(
        problem=problem_info)
    encounter_ids = [long(x.encounter.id) for x in encounter_records]

    related_encounters = Encounter.objects.filter(id__in=encounter_ids)

    related_encounter_holder = EncounterSerializer(
        related_encounters, many=True).data

    observations = Observation.objects.filter(problem=problem_info)
    observations_holder = []
    for observation in observations:
        observation_dict = ObservationSerializer(observation).data
        observations_holder.append(observation_dict)

    sharing_patients = SharingPatient.objects.filter(shared=patient).order_by('sharing__first_name', 'sharing__last_name')

    sharing_patients_list = []
    for sharing_patient in sharing_patients:
        user_dict = UserProfileSerializer(sharing_patient.sharing.profile).data
        user_dict['problems'] = [x.id for x in sharing_patient.problems.all()]
        sharing_patients_list.append(user_dict)

    resp = {}
    resp['success'] = True
    resp['info'] = problem_dict
    resp['patient_notes'] = patient_note_holder
    resp['physician_notes'] = physician_note_holder
    resp['problem_goals'] = problem_goals_holder
    resp['problem_todos'] = problem_todos_holder
    resp['problem_images'] = problem_images_holder

    resp['effecting_problems'] = effecting_problems_holder
    resp['effected_problems'] = effected_problems_holder
    resp['patient_problems'] = patient_problems_holder
    resp['history_note'] = history_note_holder
    resp['wiki_notes'] = wiki_notes_holder
    resp['activities'] = activity_holder

    resp['related_encounters'] = related_encounter_holder
    resp['observations'] = observations_holder

    resp['sharing_patients'] = sharing_patients_list

    return ajax_response(resp)


@login_required
def get_problem_activity(request, problem_id, last_id):
    resp = {}
    resp['success'] = False

    try:
        problem = Problem.objects.get(id=problem_id)
    except Problem.DoesNotExist:
        raise Http404("Problem DoesNotExist")

    activites = ProblemActivity.objects.filter(problem=problem).filter(id__gt=last_id)
    activity_holder = ProblemActivitySerializer(activites, many=True).data
    resp['activities'] = activity_holder
    resp['success'] = True

    return ajax_response(resp)


# Problem
@login_required
def add_patient_problem(request, patient_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_problem']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:

        term = request.POST.get('term')
        concept_id = request.POST.get('code', None)

        patient = User.objects.get(id=patient_id)

        problem_exists = Problem.objects.filter(
            problem_name=term, patient=patient).exists()

        if problem_exists is not True:

            new_problem = Problem(
                patient=patient, problem_name=term, concept_id=concept_id)
            if actor_profile.role == 'physician' or actor_profile.role == 'admin':
                new_problem.authenticated = True

            new_problem.save()

            physician = request.user

            summary = 'Added <u>problem</u> <b>%s</b>' % term
            op_add_event(physician, patient, summary, new_problem)

            activity = "Added <u>problem</u>: <b>%s</b>" % term
            add_problem_activity(new_problem, actor_profile, activity)

            new_problem_dict = ProblemSerializer(new_problem).data

            resp['success'] = True
            resp['problem'] = new_problem_dict

            # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
            if concept_id in ['73211009', '46635009', '44054006']:
                observation = Observation()
                observation.problem = new_problem
                observation.subject = new_problem.patient.profile
                observation.save()

        else:
            resp['msg'] = 'Problem already added'

    return ajax_response(resp)


@login_required
def change_name(request, problem_id):

    resp = {}
    resp['success'] = False

    permissions = ['change_problem_name']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:

        term = request.POST.get('term')
        concept_id = request.POST.get('code', None)

        problem = Problem.objects.get(id=problem_id)
        old_problem_name = problem.problem_name
        old_problem_concept_id = problem.concept_id
        problem_exists = Problem.objects.filter(
            problem_name=term, patient=problem.patient).exists()

        if problem_exists is not True:

            problem.problem_name = term
            if concept_id:
                problem.concept_id = concept_id
            else:
                problem.concept_id = None

            if datetime.now() > datetime.strptime(problem.start_date.strftime('%d/%m/%Y') + ' ' + problem.start_time.strftime('%H:%M:%S'), "%d/%m/%Y %H:%M:%S") + timedelta(hours=24):
                problem.old_problem_name = old_problem_name

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

            new_problem_dict = ProblemSerializer(problem).data

            resp['success'] = True
            resp['problem'] = new_problem_dict

            # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
            # if concept_id in ['73211009', '46635009', '44054006']:
            #     observation = Observation()
            #     observation.problem = problem
            #     observation.subject = problem.patient.profile
            #     observation.save()

        else:
            resp['msg'] = 'Problem already added'

    return ajax_response(resp)

# Problems
@login_required
def update_problem_status(request, problem_id):
    # Different permissions for different cases
    # Modify this view

    resp = {}

    resp['success'] = False

    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    problem = Problem.objects.get(id=problem_id)
    patient = problem.patient

    is_controlled = request.POST.get('is_controlled') == 'true'
    is_active = request.POST.get('is_active') == 'true'
    authenticated = request.POST.get('authenticated') == 'true'

    problem.is_controlled = is_controlled
    problem.is_active = is_active
    problem.authenticated = authenticated

    problem.save()

    status_labels = {}
    status_labels['problem_name'] = problem.problem_name

    if is_controlled:
        status_labels['is_controlled'] = 'controlled'
    else:
        status_labels['is_controlled'] = 'not controlled'

    if is_active:
        status_labels['is_active'] = "active"
    else:
        status_labels['is_active'] = 'not_active'

    if authenticated:
        status_labels['authenticated'] = "authenticated"
    else:
        status_labels['authenticated'] = 'not_authenticated'

    physician = request.user

    summary = """Changed <u>problem</u>: <b>%(problem_name)s</b> status to : <b>%(is_controlled)s</b> ,<b>%(is_active)s</b> ,<b>%(authenticated)s</b>""" % status_labels
    op_add_event(physician, patient, summary, problem)

    activity = summary
    add_problem_activity(problem, actor_profile, activity)

    resp['success'] = True

    return ajax_response(resp)


# Problems
@login_required
def update_start_date(request, problem_id):

    resp = {}

    resp['success'] = False

    permissions = ['modify_problem']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        start_date = request.POST.get('start_date')
        problem.start_date = get_new_date(start_date)

        problem.save()

        physician = request.user

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

    if request.method == 'POST' and permitted:
        note = request.POST.get('note')
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            problem = None

        if problem is not None:

            new_note = ProblemNote(
                author=actor_profile, problem=problem,
                note=note, note_type='history')

            new_note.save()

            activity = 'Added History Note  <b>%s</b>' % note
            add_problem_activity(problem, actor_profile, activity, 'input')

            physician = request.user
            patient = problem.patient
            op_add_event(physician, patient, activity, problem)

            new_note_dict = ProblemNoteSerializer(new_note).data
            resp['note'] = new_note_dict

            resp['success'] = True

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
        except Problem.DoesNotExist:
            problem = None
        except UserProfile.DoesNotExist:
            author = None

        if problem is not None and author is not None:

            new_note = ProblemNote(
                author=author, problem=problem,
                note=note, note_type='wiki')

            new_note.save()

            activity = 'Added wiki note: <b>%s</b>' % note
            add_problem_activity(problem, actor_profile, activity, 'input')

            physician = request.user
            patient = problem.patient
            op_add_event(physician, patient, activity, problem)

            new_note_dict = ProblemNoteSerializer(new_note).data
            resp['note'] = new_note_dict

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