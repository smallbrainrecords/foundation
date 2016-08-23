from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import MyStoryTab, MyStoryTextComponent, MyStoryTextComponentEntry
from .serializers import MyStoryTextComponentEntrySerializer, MyStoryTextComponentSerializer, MyStoryTabSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
from users_app.views import permissions_accessed


@login_required
def track_tab_click(request, tab_id):
    resp = {}
    resp['success'] = False
    tab_info = MyStoryTab.objects.get(id=tab_id)
    if permissions_accessed(request.user, tab_info.patient.id):
        actor = request.user
        patient = tab_info.patient

        summary = "<b>%s</b> accessed %s" % (actor.username, tab_info.name)
        op_add_event(actor, patient, summary)
        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_my_story(request, patient_id):
    resp = {}
    resp['success'] = False
    
    if permissions_accessed(request.user, int(patient_id)):
        tabs = MyStoryTab.objects.filter(patient_id=int(patient_id))
        resp['success'] = True
        resp['info'] = MyStoryTabSerializer(tabs, many=True).data
    return ajax_response(resp)

@login_required
def get_tab_info(request, tab_id):
    resp = {}
    resp['success'] = False
    tab_info = MyStoryTab.objects.get(id=tab_id)
    if permissions_accessed(request.user, tab_info.patient.id):
        resp['success'] = True
        resp['info'] = MyStoryTabSerializer(tab_info).data
    return ajax_response(resp)

@login_required
@api_view(["POST"])
@permissions_required(["add_my_story_tab"])
def add_tab(request, patient_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        tab = MyStoryTab.objects.create(patient_id=int(patient_id),
                                       author=request.user,
                                       name=request.POST.get("name", None))

        private = True if request.POST.get('private', False) else False
        tab.private = private
        tab.save()

        resp['tab'] = MyStoryTabSerializer(tab).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
def delete_study(request, study_id):
    resp = {}
    resp['success'] = False
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.user.id):
        study.delete()

        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_study_info(request, study_id):
    resp = {}
    resp['success'] = False
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.user.id):
        resp['info'] = ColonCancerStudySerializer(study).data
    return ajax_response(resp)

@login_required
@api_view(["POST"])
def edit_study(request, study_id):
    resp = {}
    resp['success'] = False
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.user.id):
        actor_profile = UserProfile.objects.get(user=request.user)
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
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.user.id):
        actor_profile = UserProfile.objects.get(user=request.user)
        study.last_updated_user = actor_profile
        study.save()

        images = request.FILES.getlist('file[]')
        for image in images:
            study_image = ColonCancerStudyImage(author=actor_profile, study=study, image=image)
            study_image.save()

            resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
def delete_study_image(request, study_id, image_id):
    resp = {}
    resp['success'] = False
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.user.id):
        actor_profile = UserProfile.objects.get(user=request.user)
        study.last_updated_user = actor_profile
        study.save()

        ColonCancerStudyImage.objects.get(id=image_id).delete()

        resp['success'] = True
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_study_image(request, study_id):
    resp = {}
    resp['success'] = False
    study = ColonCancerStudy.objects.get(id=study_id)
    if permissions_accessed(request.user, study.author.user.id):
        if request.FILES:
            actor_profile = UserProfile.objects.get(user=request.user)
            study.last_updated_user = actor_profile
            study.save()

            image = ColonCancerStudyImage.objects.create(study_id=study_id, author=actor_profile, image=request.FILES['0'])

            image_dict = {
                'image': image.filename(),
                'datetime': datetime.strftime(image.datetime, '%Y-%m-%d'),
                'id': image.id,
                'author': UserProfileSerializer(image.author).data,
                'study': ColonCancerStudySerializer(image.study).data,
            }
            resp['image'] = image_dict
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
def add_factor(request, colon_id):
    resp = {}
    resp['success'] = False
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.user.id):
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

            if RiskFactor.objects.filter(colon=colon).count() == 1 and request.POST.get("value", None) == 'no known risk':
                colon.risk = 'normal'
            else:
                colon.risk = 'high'
            colon.last_risk_updated_user = actor_profile
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
    resp = {}
    resp['success'] = False
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.user.id):
        actor_profile = UserProfile.objects.get(user=request.user)

        if RiskFactor.objects.filter(colon=colon, factor=request.POST.get("value", None)).exists():
            factor = RiskFactor.objects.get(colon=colon, factor=request.POST.get("value", None))
            factor.delete()

            if not RiskFactor.objects.filter(colon=colon) or (RiskFactor.objects.filter(colon=colon).count() == 1 and RiskFactor.objects.filter(colon=colon, factor='no known risk').exists()):
                colon.risk = 'normal'
                colon.last_risk_updated_user = actor_profile
                colon.last_risk_updated_date = datetime.now().date()
                colon.todo_past_five_years = False
                colon.save()
            resp['info'] = ColonCancerScreeningSerializer(colon).data
            resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
def refuse(request, colon_id):
    resp = {}
    resp['success'] = False
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.user.id):
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
    resp = {}
    resp['success'] = False
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.user.id):
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
    resp = {}
    resp['success'] = False
    colon = ColonCancerScreening.objects.get(id=colon_id)
    if permissions_accessed(request.user, colon.patient.user.id):
        note = request.POST.get("note")
        colon_note = ColonCancerTextNote.objects.create(colon_id=colon_id, author=request.user.profile, note=note)

        resp['note'] = ColonCancerTextNoteSerializer(colon_note).data
        resp['success'] = True
    return ajax_response(resp)

@login_required
def edit_note(request, note_id):
    resp = {}
    resp['success'] = False
    note = ColonCancerTextNote.objects.get(id=note_id)
    if permissions_accessed(request.user, note.author.user.id):
        note.note = request.POST.get('note')
        note.save()
        resp['success'] = True
        resp['note'] = ColonCancerTextNoteSerializer(note).data
    return ajax_response(resp)

@login_required
def delete_note(request, note_id):
    resp = {}
    resp['success'] = False
    note = ColonCancerTextNote.objects.get(id=note_id)
    if permissions_accessed(request.user, note.author.user.id):
        note.delete()
        resp['success'] = True
    return ajax_response(resp)