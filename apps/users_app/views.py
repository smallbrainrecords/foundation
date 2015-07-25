from common.views import *

from emr.models import UserProfile, AccessLog, Problem, \
 Goal, ToDo, Guideline, TextNote, PatientImage, \
 Encounter, EncounterEvent,  Sharing, Viewer, \
 ViewStatus, ProblemRelationship



from pain.models import PainAvatar

import project.settings as settings

from problems_app.serializers import ProblemSerializer
from goals_app.serializers import GoalSerializer
from .serializers import UserProfileSerializer
from todo_app.serializers import TodoSerializer
from encounters_app.serializers import EncounterSerializer

import logging

def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except:
        return False


# Users
@login_required
def manage_patient(request, user_id):
    role = UserProfile.objects.get(user=request.user).role
    
    
    user = User.objects.get(id=user_id)
    actor_profile = UserProfile.objects.get(user=request.user)
    patient_profile = UserProfile.objects.get(user=user)

    # allowed viewers are the patient, admin/physician, and other patients the patient has shared to
    if (not ((request.user == user) or (role in ['admin', 'physician']) or (Sharing.objects.filter(patient=user, other_patient=request.user, all=True)))):
        return HttpResponse("Not allowed")
    if (not is_patient(user)):
        return HttpResponse("Error: this user isn't a patient")

    context = {}


    context['patient'] = user
    context['user_role']  = actor_profile.role
    context['patient_profile'] = patient_profile

    context = RequestContext(request, context)


    return render_to_response("manage_patient.html", context)


# Users
@login_required
def get_patient_info(request, patient_id):

    patient_user = User.objects.get(id=patient_id)
    patient_profile = UserProfile.objects.get(user=patient_user)

    # Active Problems
    problems = Problem.objects.filter(patient=patient_user, is_active=True)
    problem_list = []
    for problem in problems:
    	problem_dict = ProblemSerializer(problem).data
        problem_list.append(problem_dict)

    # Inactive Problems
    inactive_problems = Problem.objects.filter(patient=patient_user, is_active=False)
    inactive_problems_list = []
    for problem in inactive_problems:
        problem_dict = ProblemSerializer(problem).data
        inactive_problems_list.append(problem_dict)

    # Not accomplished Goals
    goals = Goal.objects.filter(patient=patient_user, accomplished=False)
    goal_list = []
    for goal in goals:
    	goal_dict = GoalSerializer(goal).data
        goal_list.append(goal_dict)


    #accomplished Goals
    completed_goals = Goal.objects.filter(patient=patient_user, accomplished=True)
    completed_goals_list = []
    for goal in completed_goals:
        goal_dict = GoalSerializer(goal).data
        completed_goals_list.append(goal_dict)



    # Not accomplished Todos
    pending_todos = ToDo.objects.filter(patient=patient_user, accomplished=False)
    pending_todo_list = []
    for todo in pending_todos:
    	todo_dict = TodoSerializer(todo).data
        pending_todo_list.append(todo_dict)

    # Accomplished Todos
    accomplished_todos = ToDo.objects.filter(patient=patient_user, accomplished=True)
    accomplished_todo_list = []
    for todo in accomplished_todos:
    	todo_dict = TodoSerializer(todo).data
        accomplished_todo_list.append(todo_dict)

    encounters = Encounter.objects.filter(
        patient=patient_user).order_by('-starttime')

    encounter_list = []
    for encounter in encounters:
    	encounter_dict = EncounterSerializer(encounter).data
        encounter_list.append(encounter_dict)


    patient_profile_dict = UserProfileSerializer(patient_profile).data

    resp = {}
    resp['info'] = patient_profile_dict
    resp['problems'] = problem_list
    resp['goals'] = goal_list
    resp['pending_todos'] = pending_todo_list
    resp['accomplished_todos'] = accomplished_todo_list
    resp['inactive_problems'] = inactive_problems_list
    resp['completed_goals'] = completed_goals_list

    resp['encounters'] = encounter_list
    return ajax_response(resp)



# Users
@login_required
def update_patient_summary(request, patient_id):

    resp = {}

    resp['success'] = False

    new_summary = request.POST.get('summary')

    patient = User.objects.get(id=patient_id)

    patient_profile = UserProfile.objects.get(user=patient, role='patient')

    patient_profile.summary = new_summary

    patient_profile.save()

    resp['success'] = True

    return ajax_response(resp)


@login_required
def fetch_active_user(request):

    user = User.objects.get(id=request.user.id)

    user_profile = UserProfile.objects.get(user=user)

    user_profile = UserProfileSerializer(user_profile).data

    resp = {}
    resp['user_profile'] = user_profile

    return ajax_response(resp)
