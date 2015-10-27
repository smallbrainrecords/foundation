from common.views import *

from emr.models import UserProfile, ToDo
from emr.operations import op_add_event

from .serializers import TodoSerializer

from emr.manage_patient_permissions import check_permissions


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


# Todos
@login_required
def add_patient_todo(request, patient_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_todo']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        todo_name = request.POST.get('name')

        patient = User.objects.get(id=patient_id)
        physician = request.user

        new_todo = ToDo(patient=patient, todo=todo_name)
        new_todo.save()

        if new_todo.problem:
            problem_name = todo.problem.problem_name
        else:
            problem_name = ''
        summary = '''
            Added <u>todo</u> <b>%s</b> for <u>problem</u> <b>%s</b>
            ''' % (todo_name, problem_name)

        op_add_event(physician, patient, summary)

        new_todo_dict = TodoSerializer(new_todo).data
        resp['todo'] = new_todo_dict
        resp['success'] = True

    return ajax_response(resp)


@login_required
def update_todo_status(request, todo_id):

    resp = {}
    resp['success'] = False
    permissions = ['set_todo_status']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == 'POST' and permitted:

        todo = ToDo.objects.get(id=todo_id)
        accomplished = request.POST.get('accomplished') == 'true'
        todo.accomplished = accomplished
        todo.save()

        physician = request.user
        patient = todo.patient

        if todo.problem:
            problem_name = todo.problem.problem_name
        else:
            problem_name = ''

        if accomplished:
            accomplished_label = 'accomplished'
        else:
            accomplished_label = 'not accomplished'

        summary = """
            Updated status of <u>todo</u> : <b>%s</b> ,
            <u>problem</u> <b>%s</b> to <b>%s</b>
            """ % (todo.todo, problem_name, accomplished_label)

        op_add_event(physician, patient, summary, todo.problem)

        resp['success'] = True

    return ajax_response(resp)
