from common.views import *

from emr.models import UserProfile, Problem
from emr.models import Goal, ToDo, TextNote, PatientImage
from emr.models import ProblemRelationship
from emr.models import ProblemNote

from emr.operations import op_add_event

from .serializers import ProblemSerializer, PatientImageSerializer
from .serializers import ProblemNoteSerializer
from emr.serializers import TextNoteSerializer
from todo_app.serializers import TodoSerializer
from goals_app.serializers import GoalSerializer

from emr.manage_patient_permissions import check_permissions


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
    resp = {}
    return ajax_response(resp)


# Problem
@login_required
def get_problem_info(request, problem_id):
    problem_info = Problem.objects.get(id=problem_id)
    patient = problem_info.patient

    # Notes - Todo
    patient_notes = []
    physician_notes = []

    problem_goals = Goal.objects.filter(problem=problem_info)
    problem_todos = ToDo.objects.filter(problem=problem_info)

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

    resp = {}
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
        concept_id = request.POST.get('code')

        patient = User.objects.get(id=patient_id)

        problem_exists = Problem.objects.filter(
            concept_id=concept_id, patient=patient).exists()

        if problem_exists is not True:

            new_problem = Problem(
                patient=patient, problem_name=term, concept_id=concept_id)
            if actor_profile.role == 'physician':
                new_problem.authenticated = True

            new_problem.save()

            physician = request.user
            summary = 'Added <u>problem</u> <b>%s</b>' % term

            op_add_event(physician, patient, summary)

            new_problem_dict = ProblemSerializer(new_problem).data

            resp['success'] = True
            resp['problem'] = new_problem_dict

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

    summary = """
        Changed <u>problem</u>: <b>%(problem_name)s</b> status to :
        <b>%(is_controlled)s</b> ,
        <b>%(is_active)s</b> ,
        <b>%(authenticated)s</b>
    """ % status_labels
    op_add_event(physician, patient, summary)

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
        problem.start_date = get_date(start_date)

        problem.save()

        physician = request.user

        summary = '''
            Changed <u>problem</u> :
            <b>%s</b> start date to <b>%s</b>
        ''' % (problem.problem_name, problem.start_date)
        op_add_event(physician, patient, summary)

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
        patient_id = request.POST.get('patient_id')
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

    if request.method == 'POST':
        patient_id = request.POST.get('patient_id')
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

    summary = '''
        Added <u>note</u> : <b>%s</b> to
        <u>problem</u> : <b>%s</b>
    ''' % (note, problem.problem_name)
    op_add_event(physician, patient, summary)

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

        summary = '''
            Added <u> goal </u> : <b>%s</b> to <u>problem</u> : <b>%s</b>
        ''' % (goal, problem.problem_name)
        op_add_event(physician, patient, summary)

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
        patient = problem.patient

        todo = request.POST.get('name')

        new_todo = ToDo(
            patient=patient, problem=problem, todo=todo)

        new_todo.save()

        physician = request.user

        summary = '''
            Added <u>todo</u> : <b>%s</b> to <u>problem</u> : <b>%s</b>
        ''' % (todo, problem.problem_name)
        op_add_event(physician, patient, summary)

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

        patient_image = PatientImage(
            patient=patient,
            problem=problem,
            image=request.FILES['file'])

        patient_image.save()

        summary = '''
            Physician added <u>image</u> to <u>problem</u>
            <b>%s</b> <br/>
            <a href="/media/%s">
            <img src="/media/%s" style="max-width:100px; max-height:100px" />
            </a>
        ''' % (problem.problem_name, patient_image.image, patient_image.image)

        op_add_event(actor, patient, summary)

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
        summary = '''
            Deleted <u>image</u> from <u>problem</u> : <b>%s</b>
            ''' % problem.problem_name
        op_add_event(physician, patient, summary)

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
        else:

            problem_relationship = ProblemRelationship.objects.get(
                source=source, target=target)

            problem_relationship.delete()

        resp['success'] = True

    return ajax_response(resp)
