"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view

from common.views import *
from emr.models import ColonCancerScreening, UserProfile, ColonCancerStudy, ColonCancerStudyImage, RiskFactor, Problem, \
    ColonCancerTextNote
from emr.operations import op_add_event
from users_app.serializers import SafeUserSerializer
from users_app.views import permissions_accessed
from .serializers import ColonCancerScreeningSerializer, ColonCancerStudySerializer, RiskFactorSerializer, \
    ColonCancerTextNoteSerializer, StudyImageSerializer


@login_required
def track_colon_click(request, colon_id):
    resp = {'success': False}
    colon_info = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon_info.patient.id):
        actor = request.user
        patient = colon_info.problem.patient

        summary = "<b>%s</b> accessed colorectal cancer screening" % (actor.username)
        op_add_event(actor, patient, summary, colon_info.problem)
        resp['success'] = True

    return ajax_response(resp)


@login_required
def get_colon_info(request, colon_id):
    resp = {'success': False}
    colon_info = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon_info.patient.id):
        if Problem.objects.filter(patient=colon_info.patient, id__in=[93761005, 93854002]).exists():
            if not RiskFactor.objects.filter(colon=colon_info, factor="personal history of colorectal cancer").exists():
                factor = RiskFactor.objects.create(colon=colon_info, factor="personal history of colorectal cancer")
                colon_info.risk = 'high'
                colon_info.save()
        if Problem.objects.filter(patient=colon_info.patient, id__in=[64766004, 34000006]).exists():
            if not RiskFactor.objects.filter(colon=colon_info,
                                             factor="personal history of ulcerative colitis or Crohn's disease").exists():
                factor = RiskFactor.objects.create(colon=colon_info,
                                                   factor="personal history of ulcerative colitis or Crohn's disease")
                colon_info.risk = 'high'
                colon_info.save()
        resp['success'] = True
        resp['info'] = ColonCancerScreeningSerializer(colon_info).data
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_study(request, colon_id):
    resp = {'success': False}
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.id):
        actor_profile = UserProfile.objects.get(user=request.user)
        study_date = datetime.strptime(request.POST.get('date'), '%m/%d/%Y').date()

        study = ColonCancerStudy.objects.create(colon=colon,
                                                finding=request.POST.get("finding", None),
                                                result=request.POST.get("result", None),
                                                note=request.POST.get("note", None),
                                                study_date=study_date,
                                                last_updated_user=request.user,
                                                author=request.user)
        study.save()

        resp['study'] = ColonCancerStudySerializer(study).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def delete_study(request, study_id):
    resp = {'success': False}
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.id):
        study.delete()

        resp['success'] = True

    return ajax_response(resp)


@login_required
def get_study_info(request, study_id):
    resp = {'success': False}
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.id):
        resp['info'] = ColonCancerStudySerializer(study).data
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def edit_study(request, study_id):
    resp = {'success': False}
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.id):
        actor_profile = UserProfile.objects.get(user=request.user)
        study.finding = request.POST.get("finding", None)
        study.result = request.POST.get("result", None)
        study.note = request.POST.get("note", None)
        study.study_date = datetime.strptime(request.POST.get('study_date'), '%m/%d/%Y').date()
        study.last_updated_user = request.user
        study.save()

        resp['success'] = True

    return ajax_response(resp)


@login_required
def upload_study_image(request, study_id):
    resp = {'success': False}
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.id):
        actor_profile = UserProfile.objects.get(user=request.user)
        study.last_updated_user = request.user
        study.save()

        images = request.FILES
        image_holder = []
        for dict in images:
            image = request.FILES[dict]
            study_image = ColonCancerStudyImage(author=request.user, study=study, image=image)
            study_image.save()

            image_holder.append(study_image)

        resp['images'] = StudyImageSerializer(image_holder, many=True).data
        resp['success'] = True
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def delete_study_image(request, study_id, image_id):
    resp = {'success': False}
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.id):
        actor_profile = UserProfile.objects.get(user=request.user)
        study.last_updated_user = request.user
        study.save()

        ColonCancerStudyImage.objects.get(id=image_id).delete()

        resp['success'] = True
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_study_image(request, study_id):
    resp = {'success': False}
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.user.id):
        if request.FILES:
            actor_profile = UserProfile.objects.get(user=request.user)
            study.last_updated_user = request.user
            study.save()

            image = ColonCancerStudyImage.objects.create(study_id=study_id, author=request.user,
                                                         image=request.FILES['0'])

            image_dict = {
                'image': image.filename(),
                'datetime': datetime.strftime(image.datetime, '%Y-%m-%d'),
                'id': image.id,
                'author': SafeUserSerializer(image.author).data,
                'study': ColonCancerStudySerializer(image.study).data,
            }
            resp['image'] = image_dict
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_factor(request, colon_id):
    resp = {'success': False}
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.id):
        actor_profile = UserProfile.objects.get(user=request.user)

        if not RiskFactor.objects.filter(colon=colon, factor=request.POST.get("value", None)).exists():
            factor = RiskFactor.objects.create(colon=colon, factor=request.POST.get("value", None))
            if factor.factor == 'no known risk':
                factors = RiskFactor.objects.filter(colon=colon).exclude(factor='no known risk')
                for f in factors:
                    f.delete()
            else:
                factors = RiskFactor.objects.filter(colon=colon, factor='no known risk')
                for f in factors:
                    f.delete()

            if RiskFactor.objects.filter(colon=colon).count() == 1 and request.POST.get("value",
                                                                                        None) == 'no known risk':
                colon.risk = 'normal'
            else:
                colon.risk = 'high'
            colon.last_risk_updated_user = request.user
            colon.last_risk_updated_date = datetime.now().date()
            colon.todo_past_five_years = False
            colon.save()
            resp['factor'] = RiskFactorSerializer(factor).data
            resp['info'] = ColonCancerScreeningSerializer(colon).data
            resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def delete_factor(request, colon_id):
    resp = {'success': False}
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.id):
        actor_profile = UserProfile.objects.get(user=request.user)

        if RiskFactor.objects.filter(colon=colon, factor=request.POST.get("value", None)).exists():
            factor = RiskFactor.objects.get(colon=colon, factor=request.POST.get("value", None))
            factor.delete()

            if not RiskFactor.objects.filter(colon=colon) or (
                    RiskFactor.objects.filter(colon=colon).count() == 1 and RiskFactor.objects.filter(
                colon=colon, factor='no known risk').exists()):
                colon.risk = 'normal'
                colon.last_risk_updated_user = request.user
                colon.last_risk_updated_date = datetime.now().date()
                colon.todo_past_five_years = False
                colon.save()
            resp['info'] = ColonCancerScreeningSerializer(colon).data
            resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def refuse(request, colon_id):
    resp = {'success': False}
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.id):
        if colon.patient_refused:
            colon.patient_refused = False
        else:
            colon.patient_refused = True
            colon.patient_refused_on = datetime.now()
        colon.save()
        colon = ColonCancerScreening.objects.get(id=colon_id)
        resp['info'] = ColonCancerScreeningSerializer(colon).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def not_appropriate(request, colon_id):
    resp = {'success': False}
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.id):
        if colon.not_appropriate:
            colon.not_appropriate = False
        else:
            colon.not_appropriate = True
            colon.not_appropriate_on = datetime.now()
        colon.save()
        colon = ColonCancerScreening.objects.get(id=colon_id)
        resp['info'] = ColonCancerScreeningSerializer(colon).data
        resp['success'] = True

    return ajax_response(resp)


# Note
@login_required
def add_note(request, colon_id):
    resp = {'success': False}
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.id):
        note = request.POST.get("note")
        colon_note = ColonCancerTextNote.objects.create(colon_id=colon_id, author=request.user, note=note)

        resp['note'] = ColonCancerTextNoteSerializer(colon_note).data
        resp['success'] = True
    return ajax_response(resp)


@login_required
def edit_note(request, note_id):
    resp = {'success': False}
    note = ColonCancerTextNote.objects.get(id=note_id)
    if permissions_accessed(request.user, note.author.id):
        note.note = request.POST.get('note')
        note.save()
        resp['success'] = True
        resp['note'] = ColonCancerTextNoteSerializer(note).data
    return ajax_response(resp)


@login_required
def delete_note(request, note_id):
    resp = {'success': False}
    note = ColonCancerTextNote.objects.get(id=note_id)
    if permissions_accessed(request.user, note.author.id):
        note.delete()
        resp['success'] = True
    return ajax_response(resp)
