from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import Observation, ObservationComponent, ObservationComponentTextNote
from emr.models import OBSERVATION_TYPES
from .serializers import ObservationComponentTextNoteSerializer, ObservationComponentSerializer, ObservationSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
from users_app.views import permissions_accessed


@login_required
def track_observation_click(request, observation_id):
    resp = {}
    resp['success'] = False
    observation = Observation.objects.get(id=observation_id)
    if permissions_accessed(request.user, observation.subject.user.id):
        actor = request.user
        patient = observation.subject.user

        summary = "<b>%s</b> accessed %s" % (actor.username, observation.name)
        op_add_event(actor, patient, summary)
        resp['success'] = True

    return ajax_response(resp)

@login_required
def get_datas(request, patient_id):
    resp = {}
    resp['success'] = False
    
    if permissions_accessed(request.user, int(patient_id)):
        observations = Observation.objects.filter(subject__user__id=int(patient_id)).exclude(name=OBSERVATION_TYPES['a1c']['name'])
        resp['success'] = True
        resp['info'] = ObservationSerializer(observations, many=True).data
    return ajax_response(resp)


@login_required
def get_observation_info(request, observation_id):
    observation = Observation.objects.get(id=observation_id)
    resp = {}
    resp['success'] = True
    resp['info'] = ObservationSerializer(observation).data
    return ajax_response(resp)