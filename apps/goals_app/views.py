from django.contrib.auth.decorators import login_required

from common.views import *
from emr.models import UserProfile, Goal, TextNote
from emr.operations import op_add_event
from emr.serializers import TextNoteSerializer
from problems_app.operations import add_problem_activity
from .serializers import GoalSerializer


# Goals
@login_required
def get_goal_info(request, goal_id):
    resp = {}
    goal = Goal.objects.get(id=goal_id)
    goal_notes = goal.notes.all().order_by('-id')
    resp['goal'] = GoalSerializer(goal).data
    resp['goal_notes'] = TextNoteSerializer(goal_notes, many=True).data
    return ajax_response(resp)


# Goals
@permissions_required(["add_goal"])
@login_required
def add_patient_goal(request, patient_id):
    goal_name = request.POST.get('name')
    new_goal = Goal.objects.create(patient_id=patient_id, goal=goal_name)

    physician = request.user
    patient = User.objects.get(id=patient_id)
    summary = 'Added <u>goal</u> <b>%s</b>' % goal_name
    op_add_event(physician, patient, summary)

    resp = {}
    resp['success'] = True
    resp['goal'] = GoalSerializer(new_goal).data
    return ajax_response(resp)


# Goals
@permissions_required(["modify_goal"])
@login_required
def update_goal_status(request, patient_id, goal_id):
    resp = {}
    patient = User.objects.get(id=patient_id)
    goal = Goal.objects.get(id=goal_id, patient=patient)

    is_controlled = request.POST.get('is_controlled') == 'true'
    accomplished = request.POST.get('accomplished') == 'true'
    goal.is_controlled = is_controlled
    goal.accomplished = accomplished
    goal.save()

    status_labels = {
        "goal": goal.goal,
        "is_controlled": "controlled" if goal.is_controlled else "not controlled",
        "accomplished": "accomplished" if goal.accomplished else "not accomplished",
        "problem": goal.problem.problem_name if goal.problem else "",
    }

    physician = request.user
    summary = "Change <u>goal</u>: <b>%(goal)s</b> <u>status</u>"
    summary += " to <b>%(is_controlled)s</b> <b>%(accomplished)s</b>"
    summary += " for <u>problem</u> <b>%(problem)s</b> "
    summary = summary % status_labels

    op_add_event(physician, patient, summary, goal.problem)

    if goal.problem:
        actor_profile = UserProfile.objects.get(user=request.user)
        add_problem_activity(goal.problem, request.user, summary, 'output')

    resp['success'] = True
    return ajax_response(resp)


# Goals
@permissions_required(["modify_goal"])
@login_required
def add_goal_note(request, patient_id, goal_id):
    resp = {}

    actor_profile = UserProfile.objects.get(user=request.user)
    goal = Goal.objects.get(id=goal_id, patient_id=patient_id)

    note = request.POST.get('new_note')
    new_note = TextNote.objects.create(note=note, by=actor_profile.role)
    goal.notes.add(new_note)

    problem_name = goal.problem.problem_name if goal.problem else "",
    summary = """
        Added <u>note</u> <b>%s</b> for <u>goal</u>:
        <b>%s</b> ,
        <u> problem </u>: <b>%s</b>
    """ % (note, goal.goal, problem_name)

    physician = request.user
    patient = goal.patient
    op_add_event(physician, patient, summary, goal.problem)

    if goal.problem:
        add_problem_activity(goal.problem, request.user, summary, 'output')

    resp['success'] = True
    resp['note'] = TextNoteSerializer(new_note).data
    return ajax_response(resp)


@permissions_required(["modify_goal"])
@login_required
def change_name(request, patient_id, goal_id):
    resp = {}
    patient = User.objects.get(id=patient_id)
    new_goal = request.POST.get("goal")

    goal = Goal.objects.get(id=goal_id, patient=patient)
    goal.goal = new_goal
    goal.save()

    status_labels = {'goal': goal.goal, 'new_goal': new_goal}

    physician = request.user
    summary = 'Change <u>goal</u>: <b>%(goal)s</b> <u>name</u> to <b>%(new_goal)s</b>'
    summary = summary % status_labels

    op_add_event(physician, patient, summary, goal.problem)

    if goal.problem:
        add_problem_activity(goal.problem, request.user, summary, 'output')

    resp['goal'] = GoalSerializer(goal).data
    resp['success'] = True
    return ajax_response(resp)
