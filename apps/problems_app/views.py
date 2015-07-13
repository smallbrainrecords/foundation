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

        new_problem = Problem(
            patient = patient,
            problem_name = term,
            concept_id = concept_id
        )

        new_problem.save()

        physician = request.user
        summary = 'Added problem %s' %term
    
        op_add_event(physician, patient, summary)

        new_problem_dict = ProblemSerializer(new_problem).data

        resp['success'] = True
        resp['problem'] = new_problem_dict

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

    resp['success'] = True

    return ajax_response(resp)

# Problems
@login_required
def add_patient_note(request, patient_id, problem_id):

    resp = {}

    resp['success'] = False
    patient = User.objects.get(id=patient_id)
    problem = Problem.objects.get(id=problem_id, patient=patient)

    note = request.POST.get('note')

    new_note = TextNote(
        by='patient',
        note=note)
    new_note.save()

    problem.notes.add(new_note)

    new_note_dict = TextNoteSerializer(new_note).data
    resp['success'] = True
    resp['note'] = new_note_dict
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


    new_note = TextNote(
        by='physician',
        note=note)
    new_note.save()

    problem.notes.add(new_note)

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


        summary='Physician added image<br/><a href="/media/%s"><img src="/media/%s" style="max-width:100px; max-height:100px" /></a>' % (
                patient_image.image, patient_image.image)

        op_add_event(actor, patient, summary)

        resp['success'] = True

    return ajax_response(resp)

# Problems
@login_required
def delete_problem_image(request, problem_id, image_id):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        image = PatientImage.objects.get(id=image_id)
        image.delete()
        resp['success'] = True

    return ajax_response(resp)


# Problems
@login_required
def unrelate_problem(request, problem_id, relationship_id):
    resp = {}
    resp['success'] = False

    if request.method == 'POST':
        relationship = ProblemRelationship.objects.get(id= relationship_id)
        relationship.delete()
        resp ['success'] = True

    return ajax_response(resp)


# Problems
@login_required
def relate_problem(request, problem_id, target_problem_id):
    resp = {}
    resp['success'] = False

    if request.method == "POST":
        source = Problem.objects.get(id=problem_id)
        target = Problem.objects.get(id=target_problem_id)

        relationship = ProblemRelationship(source=source, target=target)
        relationship.save()

        relationship_dict = ProblemRelationshipSerializer(relationship).data

        resp['success'] = True
        resp['relationship'] = relationship_dict

    return ajax_response(resp)

