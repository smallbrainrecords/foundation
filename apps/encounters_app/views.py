from rest_framework.decorators import api_view
from datetime import datetime, timedelta
from common.views import *

from emr.models import UserProfile, Encounter, EncounterEvent
from emr.models import EncounterProblemRecord, Problem

from .serializers import EncounterSerializer, EncounterEventSerializer
from problems_app.serializers import ProblemSerializer


# Encounter
@login_required
def get_encounter_info(request, encounter_id):
    encounter = Encounter.objects.get(id=encounter_id)
    encounter_events = EncounterEvent.objects.filter(encounter=encounter).order_by('datetime')
    related_problem_records = EncounterProblemRecord.objects.filter(encounter=encounter)
    related_problems = [x.problem for x in related_problem_records]

    encounter_dict = EncounterSerializer(encounter).data
    encounter_events_holder = EncounterEventSerializer(encounter_events, many=True).data
    related_problem_holder = ProblemSerializer(related_problems, many=True).data

    resp = {}
    resp['encounter'] = encounter_dict
    resp['encounter_events'] = encounter_events_holder
    resp['related_problems'] = related_problem_holder

    return ajax_response(resp)


# Encounter
@login_required
@permissions_required(["add_goal"])
def patient_encounter_status(request, patient_id):
    encounter_active = False
    current_encounter = None

    physician = request.user
    latest_encounter = Encounter.objects.filter(physician=physician,
                                                patient_id=patient_id
                                        ).order_by('-starttime').first()

    if latest_encounter and latest_encounter.stoptime is None:
        encounter_active = True
        current_encounter = EncounterSerializer(latest_encounter).data

    resp = {}
    resp['current_encounter'] = current_encounter
    resp['encounter_active'] = encounter_active
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def create_new_encounter(request, patient_id):
    encounter = Encounter.objects.create_new_encounter(patient_id, request.user)
    resp = {}
    resp['success'] = True
    resp['encounter'] = EncounterSerializer(encounter).data
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
def stop_patient_encounter(request, encounter_id):
    physician = request.user
    Encounter.objects.stop_patient_encounter(physician, encounter_id)
    resp = {}
    resp['success'] = True
    resp['msg'] = 'Encounter is stopped'
    return ajax_response(resp)


# Encounter
@permissions_required(["add_event_summary"])
@login_required
@api_view(["POST"])
def add_event_summary(request):
    resp = {}
    physician = request.user
    encounter_id = request.POST.get('encounter_id')
    event_summary = request.POST.get('event_summary')
    encounter_event = Encounter.objects.add_event_summary(encounter_id, physician, event_summary)
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def update_encounter_note(request, patient_id, encounter_id):
    note = request.POST.get('note')
    Encounter.objects.filter(id=encounter_id).update(note=note)
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def upload_encounter_audio(request, patient_id, encounter_id):
    audio_file = request.FILES['file']
    Encounter.objects.filter(id=encounter_id).update(audio=audio_file)
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def upload_encounter_video(request, patient_id, encounter_id):
    video_file = request.FILES['file']
    Encounter.objects.filter(id=encounter_id).update(video=video_file)
    resp = {}
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter_timestamp"])
@login_required
@api_view(["POST"])
def add_timestamp(request, patient_id, encounter_id):
    timestamp = request.POST.get('timestamp', 0)
    encounter_event = Encounter.objects.add_timestamp(encounter_id, request.user, round(float(timestamp)))
    resp = {}
    resp['success'] = True
    resp['encounter_event'] = EncounterEventSerializer(encounter_event).data
    return ajax_response(resp)

# Encounter
@permissions_required(["add_encounter_timestamp"])
@login_required
@api_view(["POST"])
def mark_favorite(request, encounter_event_id):
    is_favorite = True if request.POST.get('is_favorite', False) == "true" else False
    EncounterEvent.objects.filter(id=encounter_event_id).update(is_favorite=is_favorite)
    resp = {}
    resp['success'] = True
    return ajax_response(resp)

@permissions_required(["add_encounter_timestamp"])
@login_required
@api_view(["POST"])
def name_favorite(request, encounter_event_id):
    name_favorite = request.POST.get("name_favorite", "")
    EncounterEvent.objects.filter(id=encounter_event_id).update(name_favorite=name_favorite)
    resp = {}
    resp['success'] = True
    return ajax_response(resp)
