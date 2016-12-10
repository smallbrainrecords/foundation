from rest_framework.decorators import api_view

from common.views import *
from emr.models import Inr, InrValue, InrTextNote, Problem
from users_app.views import permissions_accessed
from .serializers import InrTextNoteSerializer, InrSerializer
from .serializers import ProblemSerializer


@login_required
def get_inrs(request, patient_id, problem_id):
    """
    Get the INR widget which is pinned to the problem(sharing problem is filtered through patient)
    :param request:
    :param patient_id:
    :param problem_id:
    :return:
    """
    resp = {'success': False}

    if permissions_accessed(request.user, int(patient_id)):
        inr = Inr.objects.filter(problem__id=problem_id, patient_id=patient_id)

    resp['success'] = True
    if inr.exists():
        resp['info'] = InrSerializer(inr.get()).data
    return ajax_response(resp)


@login_required
def set_target(request, inr_id):
    resp = {}
    resp['success'] = True
    try:
        Inr.objects.filter(id=inr_id).update(target=request.GET['target'])
    except:
        resp['success'] = False
    return ajax_response(resp)


@login_required
@api_view(['GET'])
def get_list_problem(request):
    resp = {}
    resp['success'] = True
    # problem = Problem.objects.filter(inr_id=request.GET['id'])
    problem = Problem.objects.filter(id__in=Inr.objects.values('problem_id'))
    resp['data'] = ProblemSerializer(problem, many=True).data
    return ajax_response(resp)


@login_required
@api_view(['POST'])
def save_inrvalue(request):
    resp = {}
    resp['success'] = True
    inrvalue = InrValue(effective_datetime=request.POST['effective_datetime'],
                        current_dose=request.POST['current_dose'], value=float(request.POST['value']),
                        new_dosage=request.POST['new_dosage'], next_inr=request.POST['next_inr'],
                        inr_id=int(request.POST['inr']), author_id=int(request.POST['author_id']), ispatient=True)
    try:
        inrvalue.save()
        resp['id'] = inrvalue.pk
    except:
        resp['success'] = False
    return ajax_response(resp)


@login_required
@api_view(['POST'])
def edit_inrvalue(request, inr_id):
    resp = {}
    resp['success'] = True
    try:
        InrValue.objects.filter(id=inr_id, ispatient=True).update(
            effective_datetime=request.POST['effective_datetime'],
            current_dose=request.POST['current_dose'],
            value=float(request.POST['value']),
            new_dosage=request.POST['new_dosage'],
            next_inr=request.POST['next_inr'])
    except:
        resp['success'] = False
    return ajax_response(resp)


@login_required
@api_view(['GET'])
def delete_inrvalue(request, inr_id):
    resp = {}
    resp['success'] = True
    try:
        InrValue.objects.get(id=inr_id, ispatient=True).delete()
    except:
        resp['success'] = False
    return ajax_response(resp)


@login_required
@api_view(['POST'])
def add_note(request):
    resp = {}
    resp['success'] = True
    note = InrTextNote(note=request.POST['note'], inr_id=request.POST['inr_id'], author=request.user.profile)
    try:
        note.save()
        resp['info'] = InrTextNoteSerializer(note).data
    except:
        resp['success'] = False
    return ajax_response(resp)
