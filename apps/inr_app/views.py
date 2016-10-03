from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import Inr, InrValue, Medication, MedicationTextNote, PatientController, UserProfile
from .serializers import MedicationTextNoteSerializer, MedicationSerializer, InrValueSerializer, InrSerializer
from emr.operations import op_add_event

from users_app.serializers import UserProfileSerializer
from users_app.views import permissions_accessed


@login_required
def get_inr(request, patient_id):
    resp = {}
    resp['success'] = False
    
    if permissions_accessed(request.user, int(patient_id)):
        try:
            inr = Inr.objects.get(patient_id=int(patient_id))
        except Inr.DoesNotExist:
            inr = Inr.objects.create(patient_id=int(patient_id))
            
        resp['success'] = True
        resp['info'] = InrSerializer(inr).data
    return ajax_response(resp)

@login_required
@api_view(["POST"])
def add_medication(request, patient_id, inr_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        # Medication.objects.filter(inr_id=inr_id).update(current=False)

        medication = Medication()
        medication.author = request.user.profile
        medication.inr_id = inr_id
        medication.name = request.POST.get("name", None)
        medication.concept_id = request.POST.get("concept_id", None)
        medication.save()

        resp['medication'] = MedicationSerializer(medication).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
def add_medication_note(request, patient_id, medication_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        medication = Medication.objects.get(id=medication_id)

        note = MedicationTextNote()
        note.author = request.user.profile
        note.note = request.POST.get("note", None)
        note.medication = medication
        note.save()

        resp['note'] = MedicationTextNoteSerializer(note).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
def edit_note(request, note_id):
    note = MedicationTextNote.objects.get(id=note_id)
    note.note = request.POST.get('note')
    note.save()

    resp = {}
    resp['note'] = MedicationTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)

@login_required
def delete_note(request, note_id):
    MedicationTextNote.objects.get(id=note_id).delete()
    resp = {}
    resp['success'] = True
    return ajax_response(resp)