from common.views import *

from emr.models import UserProfile, Encounter, EncounterEvent

from .serializers import EncounterSerializer, EncounterEventSerializer

from emr.manage_patient_permissions import check_permissions


def is_patient(user):
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.role == 'patient'
    except UserProfile.DoesNotExist:
        return False


# Encounter
@login_required
def get_encounter_info(request, encounter_id):

    encounter = Encounter.objects.get(id=encounter_id)

    encounter_events = EncounterEvent.objects.filter(
        encounter=encounter).order_by('datetime')

    encounter_events_holder = []

    for event in encounter_events:
        event_dict = EncounterEventSerializer(event).data
        encounter_events_holder.append(event_dict)

    encounter_dict = EncounterSerializer(encounter).data
    resp = {}
    resp['encounter'] = encounter_dict
    resp['encounter_events'] = encounter_events_holder

    return ajax_response(resp)


# Encounter
@login_required
def patient_encounter_status(request, patient_id):

    encounter_active = False
    current_encounter = None
    permissions = ['add_encounter']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:
        physician = request.user
        patient = User.objects.get(id=patient_id)

        latest_encounter = Encounter.objects.filter(
            physician=physician,
            patient=patient).order_by('-starttime')

        if latest_encounter.exists():
            latest_encounter = latest_encounter[0]

            if latest_encounter.stoptime is None:
                encounter_active = True
                latest_encounter_dict = EncounterSerializer(
                    latest_encounter).data
                current_encounter = latest_encounter_dict

    resp = {}
    resp['permitted'] = permitted
    resp['current_encounter'] = current_encounter
    resp['encounter_active'] = encounter_active
    return ajax_response(resp)


# Encounter
@login_required
def create_new_encounter(request, patient_id):

    resp = {}
    if request.method == 'POST':

        permissions = ['add_encounter']
        actor_profile, permitted = check_permissions(permissions, request.user)

        if permitted:
            physician = request.user
            patient = User.objects.get(id=patient_id)
            # You may want to tell user that if already an encounter is running
            encounter = Encounter(
                patient=patient, physician=request.user)
            encounter.save()

            # Add event started encounter
            event_summary = 'Started encounter by <b>%s</b>' % (
                physician.username)
            encounter_event = EncounterEvent(
                encounter=encounter,
                summary=event_summary)

            encounter_event.save()

            encounter_dict = EncounterSerializer(encounter).data
            resp['success'] = True
            resp['encounter'] = encounter_dict

    return ajax_response(resp)


# Encounter
@login_required
def stop_patient_encounter(request, encounter_id):

    physician = request.user

    permissions = ['add_encounter']
    actor_profile, permitted = check_permissions(permissions, request.user)

    if permitted:

        latest_encounter = Encounter.objects.get(
            physician=physician, id=encounter_id)

        latest_encounter.stoptime = datetime.now()
        latest_encounter.save()

        event_summary = 'Stopped encounter by <b>%s</b>' % physician.username
        encounter_event = EncounterEvent(
            encounter=latest_encounter, summary=event_summary)

        encounter_event.save()

        resp = {}
        resp['success'] = True
        resp['msg'] = 'Encounter is stopped'

    return ajax_response(resp)


# Encounter
@login_required
def add_event_summary(request):

    resp = {}

    permissions = ['add_event_summary']

    actor_profile, permitted = check_permissions(permissions, request.user)
    if request.method == 'POST' and permitted:

        physician = request.user
        encounter_id = request.POST.get('encounter_id')
        event_summary = request.POST.get('event_summary')

        latest_encounter = Encounter.objects.get(
            physician=physician,
            id=encounter_id)

        encounter_event = EncounterEvent(
            encounter=latest_encounter,
            summary=event_summary)

        encounter_event.save()

        resp['success'] = True
    return ajax_response(resp)


# Encounter
@login_required
def update_encounter_note(request, patient_id, encounter_id):
    resp = {}
    resp['success'] = False

    permissions = ['add_encounter']

    actor_profile, permitted = check_permissions(permissions, request.user)

    if request.method == "POST" and permitted:
        note = request.POST.get('note')
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.note = note
        encounter.save()

        resp['success'] = True

    return ajax_response(resp)


# Encounter
@login_required
def upload_encounter_audio(request, patient_id, encounter_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_encounter']

    actor_profile, permitted = check_permissions(permissions, request.user)

    audio_file = request.FILES['file']

    if request.method == 'POST' and permitted:
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.audio = audio_file
        encounter.save()

        resp['success'] = True

    return ajax_response(resp)


# Encounter
@login_required
def upload_encounter_video(request, patient_id, encounter_id):

    resp = {}
    resp['success'] = False

    permissions = ['add_encounter']

    actor_profile, permitted = check_permissions(permissions, request.user)

    video_file = request.FILES['file']

    if request.method == 'POST' and permitted:
        encounter = Encounter.objects.get(id=encounter_id)
        encounter.video = video_file
        encounter.save()

    return ajax_response(resp)
