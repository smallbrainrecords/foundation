from django.db.models import F
from rest_framework.decorators import api_view

from common.views import *
from emr.models import Encounter, EncounterEvent
from emr.models import EncounterProblemRecord
from problems_app.serializers import ProblemSerializer
from .serializers import EncounterSerializer, EncounterEventSerializer


# Encounter
@login_required
def get_encounter_info(request, encounter_id):
    resp = {}
    encounter = Encounter.objects.get(id=encounter_id)
    encounter_events = EncounterEvent.objects.filter(encounter=encounter).order_by('datetime')
    related_problem_records = EncounterProblemRecord.objects.filter(encounter=encounter)
    related_problems = [x.problem for x in related_problem_records]
    encounter_documents = encounter.encounter_document.all()

    encounter_dict = EncounterSerializer(encounter).data
    encounter_events_holder = EncounterEventSerializer(encounter_events, many=True).data

    encounter_documents_holder = []
    for document in encounter_documents:
        encounter_documents_holder.append({
            'name': document.component.__str__(),
            'value': '%g' % float(document.value_quantity),
            'effective': document.effective_datetime.isoformat()
        })

    related_problem_holder = ProblemSerializer(related_problems, many=True).data

    resp['encounter'] = encounter_dict
    resp['encounter_events'] = encounter_events_holder
    resp['encounter_documents'] = encounter_documents_holder
    resp['related_problems'] = related_problem_holder

    return ajax_response(resp)


# Encounter
@login_required
@permissions_required(["add_encounter"])
def patient_encounter_status(request, patient_id):
    """
    Get patient latest encounter information
    :param request:
    :param patient_id:
    :return:
    """
    resp = {'success': False}
    encounter_active = False
    current_encounter = None

    physician = request.user
    latest_encounter = Encounter.objects.filter(physician=physician, patient_id=patient_id).order_by(
        '-starttime').first()

    if latest_encounter and latest_encounter.stoptime is None:
        encounter_active = True
        current_encounter = EncounterSerializer(latest_encounter).data

    resp['success'] = True
    resp['current_encounter'] = current_encounter
    resp['encounter_active'] = encounter_active
    resp['permitted'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def create_new_encounter(request, patient_id):
    resp = {'success': False}

    # Stop all encounter which currently applied to patient or physician or midlevel
    patient_encounter = Encounter.objects.filter(patient_id=patient_id).filter(stoptime=None)
    physician_encounter = Encounter.objects.filter(physician=request.user).filter(stoptime=None)

    if patient_encounter.exists():
        encounter = patient_encounter.get()
        resp['message'] = "This patient is having an active encounter by <b>{0}</b>".format(
            encounter.physician.get_full_name())
        return ajax_response(resp)

    if physician_encounter.exists():
        encounter = physician_encounter.get()
        resp['message'] = "You are having an active encounter for <b>{0}<b>. Please stop it first".format(
            encounter.patient.get_full_name())
        return ajax_response(resp)

    encounter = Encounter.objects.create_new_encounter(patient_id, request.user)
    resp['success'] = True
    resp['encounter'] = EncounterSerializer(encounter).data
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
def stop_patient_encounter(request, encounter_id):
    resp = {'success': False}
    if not Encounter.objects.filter(id=encounter_id, stoptime=None).exists():
        resp['msg'] = 'Encounter is already stopped'
        return ajax_response(resp)

    Encounter.objects.stop_patient_encounter(request.user, encounter_id)

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
    Encounter.objects.add_event_summary(encounter_id, physician, event_summary)
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def update_encounter_note(request, patient_id, encounter_id):
    resp = {}
    note = request.POST.get('note')
    Encounter.objects.filter(id=encounter_id).update(note=note)
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def upload_encounter_audio(request, patient_id, encounter_id):
    resp = {}
    audio_file = request.FILES['file']
    enc = Encounter.objects.get(id=encounter_id)
    enc.audio = audio_file
    enc.save()
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter"])
@login_required
@api_view(["POST"])
def upload_encounter_video(request, patient_id, encounter_id):
    resp = {}
    video_file = request.FILES['file']
    enc = Encounter.objects.get(id=encounter_id)
    enc.video = video_file
    enc.save()
    resp['success'] = True
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter_timestamp"])
@login_required
@api_view(["POST"])
def add_timestamp(request, patient_id, encounter_id):
    resp = {}
    timestamp = request.POST.get('timestamp', 0)
    encounter_event = Encounter.objects.add_timestamp(encounter_id, request.user, round(float(timestamp)))
    resp['success'] = True
    resp['encounter_event'] = EncounterEventSerializer(encounter_event).data
    return ajax_response(resp)


# Encounter
@permissions_required(["add_encounter_timestamp"])
@login_required
@api_view(["POST"])
def mark_favorite(request, encounter_event_id):
    resp = {}
    is_favorite = True if request.POST.get('is_favorite', False) == "true" else False
    EncounterEvent.objects.filter(id=encounter_event_id).update(is_favorite=is_favorite)
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_encounter_timestamp"])
@login_required
@api_view(["POST"])
def name_favorite(request, encounter_event_id):
    resp = {}
    name_favorite = request.POST.get("name_favorite", "")
    EncounterEvent.objects.filter(id=encounter_event_id).update(name_favorite=name_favorite)
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_encounter"])
@login_required
@api_view(["POST"])
def delete_encounter(request, patient_id, encounter_id):
    Encounter.objects.get(id=encounter_id).delete()
    resp = {'success': True}
    return ajax_response(resp)


@login_required
def increase_audio_played_count(request, encounter_id):
    resp = {}
    Encounter.objects.filter(id=encounter_id).update(audio_played_count=F('audio_played_count') + 1)
    resp['success'] = True
    return ajax_response(resp)


@login_required
@permissions_required(["add_encounter_timestamp"])
@api_view(["POST"])
def add_encounter_event(request, encounter_id):
    """
    Add encounter event
    :param request:
    :return:
    """
    resp = {'success': False}
    summary = request.POST.get('event', "")
    EncounterEvent.objects.create(encounter_id=encounter_id, summary=summary)

    resp['success'] = True
    return ajax_response(resp)


@login_required
def toggle_encounter_recorder(request, encounter_id):
    """
    Update encounter's recorder status and make a timestamp
    :param request:
    :param encounter_id:
    :return:
    """
    resp = {'success': False}
    status = request.POST.get('status')
    timestamp = request.POST.get('timestamp', 0)
    summary = request.POST.get('summary', "")

    # Update status
    Encounter.objects.filter(id=encounter_id).update(recorder_status=status)

    # Create a timestamp object
    encounter = Encounter.objects.get(id=encounter_id)
    EncounterEvent.objects.create(encounter=encounter, summary=summary,
                                  timestamp=encounter.starttime + timedelta(seconds=round(float(timestamp))))

    # Return object data
    resp['success'] = True
    resp['current_encounter'] = EncounterSerializer(encounter).data
    return ajax_response(resp)
