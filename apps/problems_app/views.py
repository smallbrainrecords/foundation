from common.views import *

from emr.models import UserProfile, AccessLog, Problem, \
 Goal, ToDo, Guideline, TextNote, PatientImage, \
 Encounter, EncounterEvent,  Sharing, Viewer, \
 ViewStatus, ProblemRelationship



from pain.models import PainAvatar

import project.settings as settings


from emr.operations import op_add_event

import logging


from .serializers import ProblemSerializer, ProblemRelationshipSerializer, PatientImageSerializer
from emr.serializers import TextNoteSerializer
from todo_app.serializers import TodoSerializer
from goals_app.serializers import GoalSerializer


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except:
        return False



@login_required
def track_problem_click(request, problem_id):
    actor = request.user
    actor_profile = UserProfile.objects.get(user=actor)

    if actor_profile.role in ['physician', 'admin']:
        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        summary = "Clicked <u>problem</u>: <b>%s</b>" %problem.problem_name
        op_add_event(actor, patient, summary)
    resp = {}
    return ajax_response(resp)


# Problem
@login_required
def get_problem_info(request, problem_id):

    

    problem_info = Problem.objects.get(id=problem_id)
    patient = problem_info.patient

    patient_notes = problem_info.notes.filter(by='patient').order_by('-id')
    physician_notes = problem_info.notes.filter(by='physician').order_by('-id')
    
    problem_goals = Goal.objects.filter(problem=problem_info)
    problem_todos = ToDo.objects.filter(problem=problem_info)

    problem_images = PatientImage.objects.filter(
        problem=problem_info)

    problem_relationships = ProblemRelationship.objects.filter(
        source=problem_info)


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

    problem_relationships_holder = []
    related_problems_ids = []
    for relationship in problem_relationships:
    	relationship_dict = ProblemRelationshipSerializer(relationship).data

        problem_relationships_holder.append(relationship_dict)
        related_problems_ids.append(relationship.target.id)


    not_related_problems = Problem.objects.filter(patient=patient).exclude(id__in=related_problems_ids)

    not_related_problems_holder = []
    for problem in not_related_problems:
    	problem_dict = ProblemSerializer(problem).data
        not_related_problems_holder.append(problem_dict)

    problem_dict = ProblemSerializer(problem_info).data



    resp = {}
    resp['info'] = problem_dict
    resp['patient_notes'] = patient_note_holder
    resp['physician_notes'] = physician_note_holder
    resp['problem_goals'] = problem_goals_holder
    resp['problem_todos'] = problem_todos_holder
    resp['problem_images'] = problem_images_holder
    resp['problem_relationships'] = problem_relationships_holder
    resp['not_related_problems'] = not_related_problems_holder
    return ajax_response(resp)



# Problem
@login_required
def add_patient_problem(request, patient_id):

    resp = {}
    resp['success'] = False


    if request.method == 'POST':

        term = request.POST.get('term')
        concept_id = request.POST.get('code')

        patient = User.objects.get(id=patient_id)


        problem_exists = Problem.objects.filter(
                concept_id=concept_id, patient=patient).exists()

        if problem_exists is not True:

            new_problem = Problem(
                patient = patient,
                problem_name = term,
                concept_id = concept_id
            )

            new_problem.save()

            physician = request.user
            summary = 'Added <u>problem</u> <b>%s</b>' %term
        
            op_add_event(physician, patient, summary)

            new_problem_dict = ProblemSerializer(new_problem).data

            resp['success'] = True
            resp['problem'] = new_problem_dict

        else:
            resp['msg'] = 'Problem already added'

    return ajax_response(resp)

# Problems
@login_required
def update_problem_status(request, patient_id, problem_id):

    resp = {}

    resp['success'] = False

    patient = User.objects.get(id=patient_id)

    problem = Problem.objects.get(id=problem_id, patient=patient)

    is_controlled = request.POST.get('is_controlled') == 'true'
    is_active = request.POST.get('is_active') == 'true'
    authenticated = request.POST.get('authenticated') == 'true'

    problem.is_controlled = is_controlled
    problem.is_active = is_active
    problem.authenticated = authenticated

    problem.save()

    status_labels = {}
    status_labels['problem_name'] = problem.problem_name
    status_labels['is_controlled'] = "controlled" if is_controlled==True else "not controlled"
    status_labels['is_active'] = "active" if is_active == True else "inactive"
    status_labels['authenticated'] = "authenticated" if authenticated == True else "not authenticated"
    

    physician = request.user

    summary = "Changed <u>problem</u>: <b>%(problem_name)s</b> status to : <b>%(is_controlled)s</b> , <b>%(is_active)s</b> , <b>%(authenticated)s</b>" %status_labels
    op_add_event(physician, patient, summary)

    resp['success'] = True

    return ajax_response(resp)


# Problems
@login_required
def update_start_date(request, patient_id, problem_id):

    resp = {}  

    resp['success'] = False

    patient = User.objects.get(id=patient_id)
    problem = Problem.objects.get(id=problem_id, patient=patient)

    start_date = request.POST.get('start_date')
    problem.start_date = get_date(start_date)

    problem.save()

    physician = request.user

    summary = "Changed <u>problem</u> : <b>%s</b> start date to <b>%s</b>" %(problem.problem_name, problem.start_date)
    op_add_event(physician, patient, summary)

    resp['success'] = True

    return ajax_response(resp)

# Problems
@login_required
def add_patient_note(request, patient_id, problem_id):

    resp = {}

    resp['success'] = False
    errors = []
    patient = User.objects.get(id=patient_id)
    patient_profile = UserProfile.objects.get(user=patient)

    problem = Problem.objects.get(id=problem_id, patient=patient)

    note = request.POST.get('note')

    if request.user == patient:
        new_note = TextNote(
            author = patient_profile,
            by='patient',
            note=note)
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
def add_physician_note(request, patient_id, problem_id):

    resp = {}
    resp['success'] = False
    patient = User.objects.get(id=patient_id)
    problem = Problem.objects.get(id=problem_id, patient=patient)

    note = request.POST.get('note')

    physician = request.user

    physician_profile = UserProfile.objects.get(user=physician)

    new_note = TextNote(
        author = physician_profile,
        by='physician',
        note=note)
    new_note.save()

    problem.notes.add(new_note)

    summary = "Added <u>note</u> : <b>%s</b> to <u>problem</u> : <b>%s</b>"  %(note, problem.problem_name)
    op_add_event(physician, patient, summary)

    new_note_dict = TextNoteSerializer(new_note).data
    resp['note'] = new_note_dict
    resp['success'] = True
    return ajax_response(resp)

# Problems
@login_required
def add_problem_goal(request, patient_id, problem_id):

    resp = {}

    resp['success'] = False

    patient = User.objects.get(id=patient_id)
    problem = Problem.objects.get(id=problem_id, patient=patient)

    goal = request.POST.get('name')

    new_goal = Goal(
            patient=patient,
            problem=problem,
            goal=goal,

        )
    new_goal.save()


    physician = request.user

    summary = "Added <u> goal </u> : <b>%s</b> to <u>problem</u> : <b>%s</b>"  %(goal, problem.problem_name)
    op_add_event(physician, patient, summary)

    new_goal_dict = GoalSerializer(new_goal).data
    resp['success'] = True
    resp['goal'] = new_goal_dict
    return ajax_response(resp)


# Problems
@login_required
def add_problem_todo(request, patient_id, problem_id):

    resp = {}
    resp['success'] = False


    patient = User.objects.get(id=patient_id)
    problem = Problem.objects.get(id=problem_id, patient=patient)

    todo = request.POST.get('name')

    new_todo = ToDo(
            patient=patient,
            problem=problem,
            todo=todo
        )

    new_todo.save()

    physician = request.user

    summary = "Added <u>todo</u> : <b>%s</b> to <u>problem</u> : <b>%s</b>"  %(todo, problem.problem_name)
    op_add_event(physician, patient, summary)


    new_todo_dict = TodoSerializer(new_todo).data

    resp['success'] = True
    resp['todo'] = new_todo_dict

    return ajax_response(resp)




# Problems
@login_required
def upload_problem_image(request, patient_id, problem_id):

    resp = {}
    resp['success'] = False

    if request.method == 'POST':

        actor = request.user
        actor_profile = UserProfile.objects.get(user=actor)

        role = actor_profile.role
        
        if role in ['physician' ,'admin']:
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


        summary='Physician added <u>image</u> to <u>problem</u> <b>%s</b> <br/><a href="/media/%s"><img src="/media/%s" style="max-width:100px; max-height:100px" /></a>' % (
                problem.problem_name, patient_image.image, patient_image.image)

        op_add_event(actor, patient, summary)

        resp['success'] = True

    return ajax_response(resp)

# Problems
@login_required
def delete_problem_image(request, problem_id, image_id):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        problem = Problem.objects.get(id=problem_id)
        patient = problem.patient

        image = PatientImage.objects.get(id=image_id)
        image.delete()

        physician = request.user
        summary = "Deleted <u>image</u> from <u>problem</u> : <b>%s</b>"  %problem.problem_name
        op_add_event(physician, patient, summary)


        resp['success'] = True

    return ajax_response(resp)






