from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *

from emr.models import ColonCancerScreening, UserProfile, ColonCancerStudy
from .serializers import ColonCancerScreeningSerializer, ColonCancerStudySerializer
from emr.operations import op_add_event

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity
from problems_app.views import permissions_required


@login_required
def get_colon_info(request, colon_id):
    colon_info = ColonCancerScreening.objects.get(id=colon_id)
    resp = {}
    resp['success'] = True
    resp['info'] = ColonCancerScreeningSerializer(colon_info).data
    return ajax_response(resp)

@login_required
def add_study(request, colon_id):
    resp = {}
    actor_profile = UserProfile.objects.get(user=request.user)
    colon = ColonCancerScreening.objects.get(id=colon_id)
    study_date = datetime.strptime(request.POST.get('date'), '%m/%d/%Y').date()

    study = ColonCancerStudy.objects.create(colon=colon,
                                           finding=request.POST.get("finding", None),
                                           result=request.POST.get("result", None),
                                           note=request.POST.get("note", None),
                                           study_date=study_date,
                                           author=actor_profile)
    study.save()

    resp['study'] = ColonCancerStudySerializer(study).data
    resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_study(request, study_id):
    resp = {}
    study = ColonCancerStudy.objects.get(id=study_id)
    study.delete()

    resp['success'] = True

    return ajax_response(resp)

@login_required
def get_study_info(request, study_id):
    resp = {}
    study = ColonCancerStudy.objects.get(id=study_id)

    resp['info'] = ColonCancerStudySerializer(study).data
    return ajax_response(resp)

@login_required
def edit_study(request, study_id):
    resp = {}
    study = ColonCancerStudy.objects.get(id=study_id)
    study.finding = request.POST.get("finding", None)
    study.result = request.POST.get("result", None)
    study.note = request.POST.get("note", None)
    study.study_date = datetime.strptime(request.POST.get('study_date'), '%m/%d/%Y').date()
    study.save()

    resp['success'] = True

    return ajax_response(resp)
