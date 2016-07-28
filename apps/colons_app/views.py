from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *

from emr.models import ColonCancerScreening, UserProfile, ColonCancerStudy, ColonCancerStudyImage, RiskFactor, Problem
from .serializers import ColonCancerScreeningSerializer, ColonCancerStudySerializer, RiskFactorSerializer
from emr.operations import op_add_event

from emr.manage_patient_permissions import check_permissions
from problems_app.operations import add_problem_activity
from problems_app.views import permissions_required
from users_app.serializers import UserProfileSerializer


@login_required
def get_colon_info(request, colon_id):
    colon_info = ColonCancerScreening.objects.get(id=colon_id)
    if Problem.objects.filter(patient=colon.patient.user, id__in=[93761005, 93854002]).exists():
        if not RiskFactor.objects.filter(colon=colon_info, factor="personal history of colorectal cancer").exists():
            factor = RiskFactor.objects.create(colon=colon_info, factor="personal history of colorectal cancer")
            colon_info.risk = 'high'
            colon_info.save()
    if Problem.objects.filter(patient=colon.patient.user, id__in=[64766004, 34000006]).exists():
        if not RiskFactor.objects.filter(colon=colon_info, factor="personal history of ulcerative colitis or Crohn's disease").exists():
            factor = RiskFactor.objects.create(colon=colon_info, factor="personal history of ulcerative colitis or Crohn's disease")
            colon_info.risk = 'high'
            colon_info.save()
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
                                           last_updated_user=actor_profile,
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
    actor_profile = UserProfile.objects.get(user=request.user)
    study = ColonCancerStudy.objects.get(id=study_id)
    study.finding = request.POST.get("finding", None)
    study.result = request.POST.get("result", None)
    study.note = request.POST.get("note", None)
    study.study_date = datetime.strptime(request.POST.get('study_date'), '%m/%d/%Y').date()
    study.last_updated_user = actor_profile
    study.save()

    resp['success'] = True

    return ajax_response(resp)

@login_required
def upload_study_image(request, study_id):
    resp = {}
    resp['success'] = False
    actor_profile = UserProfile.objects.get(user=request.user)
    study = ColonCancerStudy.objects.get(id=study_id)
    study.last_updated_user = actor_profile
    study.save()

    images = request.FILES.getlist('file[]')
    for image in images:
        study_image = ColonCancerStudyImage(author=actor_profile, study=study, image=image)
        study_image.save()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_study_image(request, study_id, image_id):
    actor_profile = UserProfile.objects.get(user=request.user)
    study = ColonCancerStudy.objects.get(id=study_id)
    study.last_updated_user = actor_profile
    study.save()

    ColonCancerStudyImage.objects.get(id=image_id).delete()

    resp = {}
    resp['success'] = True
    return ajax_response(resp)


@login_required
def add_study_image(request, study_id):
    actor_profile = UserProfile.objects.get(user=request.user)
    study = ColonCancerStudy.objects.get(id=study_id)
    study.last_updated_user = actor_profile
    study.save()

    image = ColonCancerStudyImage.objects.create(study_id=study_id, author=actor_profile, image=request.FILES['0'])
    resp = {}
    resp['success'] = True

    image_dict = {
        'image': image.filename(),
        'datetime': datetime.strftime(image.datetime, '%Y-%m-%d'),
        'id': image.id,
        'author': UserProfileSerializer(image.author).data,
        'study': ColonCancerStudySerializer(image.study).data,
    }
    resp['image'] = image_dict

    return ajax_response(resp)

@login_required
def add_factor(request, colon_id):
    resp = {}
    actor_profile = UserProfile.objects.get(user=request.user)
    colon = ColonCancerScreening.objects.get(id=colon_id)

    if not RiskFactor.objects.filter(colon=colon, factor=request.POST.get("value", None)).exists():
        factor = RiskFactor.objects.create(colon=colon, factor=request.POST.get("value", None))
        colon.risk = 'high'
        colon.last_risk_updated_user = actor_profile
        colon.last_risk_updated_date = datetime.now().date()
        colon.save()
        resp['factor'] = RiskFactorSerializer(factor).data
        resp['info'] = ColonCancerScreeningSerializer(colon).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
def delete_factor(request, colon_id):
    resp = {}
    actor_profile = UserProfile.objects.get(user=request.user)
    colon = ColonCancerScreening.objects.get(id=colon_id)

    if RiskFactor.objects.filter(colon=colon, factor=request.POST.get("value", None)).exists():
        factor = RiskFactor.objects.get(colon=colon, factor=request.POST.get("value", None))
        factor.delete()

        if not RiskFactor.objects.filter(colon=colon):
            colon.risk = 'normal'
            colon.last_risk_updated_user = actor_profile
            colon.last_risk_updated_date = datetime.now().date()
            colon.save()
        resp['info'] = ColonCancerScreeningSerializer(colon).data
        resp['success'] = True

    return ajax_response(resp)
