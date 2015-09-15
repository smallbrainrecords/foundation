from common.views import *

from emr.models import UserProfile, Goal, TextNote


from emr.operations import op_add_event

from .serializers import GoalSerializer
from emr.serializers import TextNoteSerializer


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except:
        return False


# Goals
@login_required
def get_goal_info(request, goal_id):

    goal = Goal.objects.get(id=goal_id)
    goal_notes = goal.notes.all().order_by('-id')

    goal_notes_holder = []
    for note in goal_notes:
        note_dict = TextNoteSerializer(note).data
        goal_notes_holder.append(note_dict)

    goal_dict = GoalSerializer(goal).data

    resp = {}
    resp['goal'] = goal_dict
    resp['goal_notes'] = goal_notes_holder

    return ajax_response(resp)


# Goals
@login_required
def add_patient_goal(request, patient_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_goal']
    actor_profile, permitted = check_permissions(permissions, request.user)

    goal_name = request.POST.get('name')

    patient = User.objects.get(id=patient_id)

    new_goal = Goal(patient=patient, goal=goal_name)
    new_goal.save()

    goal_dict = GoalSerializer(new_goal).data

    physician = request.user
    summary = 'Added <u>goal</u> <b>%s</b>' % goal_name

    op_add_event(physician, patient, summary)

    resp['success'] = True
    resp['goal'] = goal_dict

    return ajax_response(resp)


# Goals
@login_required
def update_goal_status(request, patient_id, goal_id):

    resp = {}
    resp['success'] = False

    permissions = ['modify_goal']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        patient = User.objects.get(id=patient_id)
        goal = Goal.objects.get(id=goal_id, patient=patient)

        is_controlled = request.POST.get('is_controlled') == 'true'
        accomplished = request.POST.get('accomplished') == 'true'

        goal.is_controlled = is_controlled
        goal.accomplished = accomplished

        goal.save()

        if goal.problem:
            problem_name = goal.problem.problem_name
        else:
            problem_name = ''

        status_labels = {}
        status_labels['goal'] = goal.goal

        if goal.is_controlled:
            status_labels['is_controlled'] = 'controlled'
        else:
            status_labels['is_controlled'] = 'not controlled'

        if goal.accomplished:
            status_labels['accomplished'] = 'accomplished'
        else:
            status_labels['accomplished'] = 'not accomplished'

        status_labels['problem'] = problem_name

        physician = request.user
        summary = "Change <u>goal</u>: <b>%(goal)s</b> <u>status</u>"
        summary += " to <b>%(is_controlled)s</b> <b>%(accomplished)s</b>"
        summary += " for <u>problem</u> <b>%(problem)s</b> "
        summary = summary % status_labels

        op_add_event(physician, patient, summary)

        resp['success'] = True

    return ajax_response(resp)


# Goals
@login_required
def add_goal_note(request, patient_id, goal_id):
    resp = {}
    resp['success'] = False

    actor = request.user

    permissions = ['modify_goal']

    actor_profile, permitted = check_permissions(permissions, actor)

    if permitted:

        patient = User.objects.get(id=patient_id)
        goal = Goal.objects.get(id=goal_id, patient=patient)

        note = request.POST.get('new_note')

        new_note = TextNote(
            note=note, by=actor_profile.role)

        new_note.save()

        goal.notes.add(new_note)

        if goal.problem:
            problem_name = goal.problem.problem_name
        else:
            problem_name = ''

        physician = request.user
        patient = goal.patient

        summary = """
            Added <u>note</u> <b>%s</b> for <u>goal</u>:
            <b>%s</b> ,
            <u> problem </u>: <b>%s</b>
        """ % (note, goal.goal, problem_name)

        op_add_event(physician, patient, summary)

        new_note_dict = TextNoteSerializer(new_note).data

        resp['success'] = True
        resp['note'] = new_note_dict

    return ajax_response(resp)
