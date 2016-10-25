from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import PatientController, UserProfile, Inr, InrValue, InrTextNote, ObservationPinToProblem
from .serializers import InrValueSerializer, InrTextNoteSerializer, InrSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
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
