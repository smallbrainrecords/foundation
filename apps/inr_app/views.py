from datetime import datetime
from django.db.models import Max, Count
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view
from rest_framework.response import Response

from emr.models import PatientController, UserProfile, Inr, InrValue, InrTextNote, ObservationPinToProblem, Problem
from .serializers import InrValueSerializer, InrTextNoteSerializer, InrSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
from .serializers import ProblemSerializer
from users_app.views import permissions_accessed

@login_required
def get_inrs(request, patient_id, problem_id):
    resp = {}
    resp['success'] = False
    
    if permissions_accessed(request.user, int(patient_id)):
        inrs = Inr.objects.filter(problem_id=problem_id)
        resp['success'] = True
        resp['info'] = InrSerializer(inrs, many=True).data
    return ajax_response(resp)

@login_required
def set_target(request, inr_id):
	resp = {}
	resp['success'] = True
	try:
		Inr.objects.filter(id=inr_id).update(target = request.GET['target'])
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
	inrvalue = InrValue(effective_datetime=request.POST['effective_datetime'], current_dose=request.POST['current_dose'], value=float(request.POST['value']), new_dosage=request.POST['new_dosage'], next_inr=request.POST['next_inr'], inr_id=int(request.POST['inr']), author_id=int(request.POST['author_id']), ispatient=True)
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
		InrValue.objects.filter(id=inr_id, ispatient=True).update(effective_datetime=request.POST['effective_datetime'], current_dose=request.POST['current_dose'], value=float(request.POST['value']), new_dosage=request.POST['new_dosage'], next_inr=request.POST['next_inr'])
	except:
		resp['success'] = False 
	return ajax_response(resp)

@login_required
@api_view(['GET'])
def delete_inrvalue(request, inr_id):
	resp = {}
	resp['success'] = True
	try:
		InrValue.objects.get(id = inr_id, ispatient=True).delete()
	except:
		resp['success'] = False 
	return ajax_response(resp)