from datetime import datetime
from django.db.models import Max
from django.core.servers.basehttp import FileWrapper
from django.http import Http404, HttpResponse
from django.db.models import Q
from common.views import *
from rest_framework.decorators import api_view

from emr.models import Inr, InrValue, Medication, MedicationTextNote, PatientController, UserProfile, MedicationPinToProblem
from .serializers import MedicationTextNoteSerializer, MedicationSerializer, InrValueSerializer, InrSerializer, MedicationPinToProblemSerializer
from emr.operations import op_add_event
from emr.mysnomedct import SnomedctConnector

from users_app.serializers import UserProfileSerializer
from users_app.views import permissions_accessed

@login_required
def list_terms(request):
    # We list snomed given a query
    query = request.GET['query']
    if query:
        query = query.replace(" ", "%")
    snomedct_conn = SnomedctConnector()
    snomedct_conn.cursor = snomedct_conn.connect()
    medications = snomedct_conn.get_medications(query)

    results_holder = json.dumps(medications)

    return HttpResponse(results_holder, content_type="application/json")


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
def get_medication(request, patient_id, medication_id):
    resp = {}
    resp['success'] = False
    
    if permissions_accessed(request.user, int(patient_id)):
        try:
            medication = Medication.objects.get(id=medication_id)
        except Medication.DoesNotExist:
            pass
            
        resp['success'] = True
        resp['info'] = MedicationSerializer(medication).data
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

@login_required
def get_pins(request, medication_id):
    pins = MedicationPinToProblem.objects.filter(medication_id=medication_id)
    resp = {}
    resp['success'] = True
    resp['pins'] = MedicationPinToProblemSerializer(pins, many=True).data
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def pin_to_problem(request, patient_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        medication_id = request.POST.get("medication_id", None)
        problem_id = request.POST.get("problem_id", None)

        try:
            pin = MedicationPinToProblem.objects.get(medication_id=medication_id, problem_id=problem_id)
            pin.delete();
        except MedicationPinToProblem.DoesNotExist:
            pin = MedicationPinToProblem(author=request.user.profile, medication_id=medication_id,
                                          problem_id=problem_id)
            pin.save()

        resp['pin'] = MedicationPinToProblemSerializer(pin).data
        resp['success'] = True

    return ajax_response(resp)

@login_required
@api_view(["POST"])
def change_active_medication(request, patient_id, medication_id):
    resp = {}
    resp['success'] = False
    if permissions_accessed(request.user, int(patient_id)):
        medication = Medication.objects.get(id=medication_id)
        medication.current = not medication.current
        medication.save()

        resp['medication'] = MedicationSerializer(medication).data
        resp['success'] = True

    return ajax_response(resp)