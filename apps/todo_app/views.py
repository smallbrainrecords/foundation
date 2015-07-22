from common.views import *

from emr.models import UserProfile, AccessLog, Problem, \
 Goal, ToDo, Guideline, TextNote, PatientImage, \
 Encounter, EncounterEvent,  Sharing, Viewer, \
 ViewStatus, ProblemRelationship



from pain.models import PainAvatar

import project.settings as settings

from emr.operations import op_add_event
import logging

from .serializers import TodoSerializer

def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except:
        return False

# Todos
@login_required
def add_patient_todo(request, patient_id):

    resp = {}
    resp['success'] = False

    todo_name = request.POST.get('name')
    todo_problem = request.POST.get('problem')

    patient = User.objects.get(id=patient_id)
    physician = request.user

    new_todo = ToDo(patient=patient, todo=todo_name)
    new_todo.save()

    summary = 'Added ToDo %s' %todo_name

    op_add_event(physician, patient, summary)

    resp['success'] = True

    new_todo_dict = TodoSerializer(new_todo).data
    resp['todo'] = new_todo_dict

    return ajax_response(resp)


@login_required
def update_todo_status(request, todo_id):

    resp = {}
    resp['success'] = False

    if request.method == 'POST':

        todo = ToDo.objects.get(id=todo_id)
        accomplished = request.POST.get('accomplished') == 'true'
        todo.accomplished = accomplished
        todo.save()

        resp['success'] = True

    return  ajax_response(resp)
