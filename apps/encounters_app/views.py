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
import os
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.forms import forms
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from pydub import AudioSegment
from rest_framework.decorators import api_view

from common.views import *
from emr.models import Encounter, EncounterEvent, EncounterProblemRecord, get_path, ObservationValue
from problems_app.serializers import ProblemSerializer
from .serializers import EncounterEventSerializer, EncounterSerializer

User = get_user_model()


# Encounter
@login_required
@timeit
def get_encounter_info(request, encounter_id):
    resp = {}
    encounter = Encounter.objects.get(id=encounter_id)
    encounter_events = EncounterEvent.objects.filter(encounter=encounter).order_by('datetime')
    related_problem_records = EncounterProblemRecord.objects.filter(encounter=encounter)
    related_problems = [x.problem for x in related_problem_records]

    encounter_dict = EncounterSerializer(encounter).data
    encounter_events_holder = EncounterEventSerializer(encounter_events, many=True).data

    # Load all data value added before and during encounter from current day to encounter document
    encounter_documents = ObservationValue.objects.filter(created_on__range=(
        encounter.starttime.replace(hour=0, minute=0, second=0, microsecond=0),
        encounter.stoptime)).filter(
        component__observation__subject=encounter.patient)  # encounter.encounter_document.all()
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
@timeit
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
@timeit
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
@timeit
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
@timeit
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
@timeit
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
@timeit
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
@timeit
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
@timeit
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
@timeit
def mark_favorite(request, encounter_event_id):
    resp = {}
    is_favorite = True if request.POST.get('is_favorite', False) == "true" else False
    EncounterEvent.objects.filter(id=encounter_event_id).update(is_favorite=is_favorite)
    resp['success'] = True
    return ajax_response(resp)


@api_view(["POST"])
@csrf_exempt
def upload_audio_chunks(request, encounter_id):
    """
    Append new chunk to audio file
    """
    # print request.POST
    form = forms.Form(request.POST, request.FILES)
    # print(form.files['data'])
    resp = {'success': False}
    enc = Encounter.objects.filter(id=encounter_id)  # TODO: filter stoptime=None
    # if not enc.exists():
    #     resp['msg'] = 'Encounter is already stopped'
    #     return ajax_response(resp)
    # else:
    #     enc = enc.first()
    enc = enc.first()

    audio_chunk = request.FILES['audio']

    sound = AudioSegment.from_file(audio_chunk, codec='opus')
    sound.export(os.path.join(settings.MEDIA_ROOT, get_path(enc, 'upload.wav')), format="wav")
    enc.audio = get_path(enc, 'upload.wav')
    enc.save()

    # if not enc.audio:
    #     print 'Init audio file'
    #
    #     from django.core.files.storage import DefaultStorage
    #     storage = DefaultStorage()
    #
    #     # audio_chunk.name = 'upload.wav'
    #     # audio = audio_chunk
    #     # enc.audio = audio
    #     # enc.save()
    #     sound = AudioSegment.from_file(audio_chunk, codec='opus')
    #     sound.export(os.path.join(settings.MEDIA_ROOT, get_path(enc, 'upload.wav')), format="wav")
    #     enc.audio = get_path(enc, 'upload.wav')
    #     enc.save()
    # else:
    #     print 'Merge audio file'
    #
    #     from django.core.files.storage import DefaultStorage
    #     storage = DefaultStorage()
    #     # f = storage.open(enc.audio.name, mode='rb')
    #     # audio = audioop.add(f.read(), audio_chunk.read(), 2)
    #     combined = AudioSegment.empty()
    #     combined += AudioSegment.from_wav(storage.open(enc.audio.name, mode='rb'))
    #
    #     print audio_chunk
    #     sound = AudioSegment.from_file(audio_chunk, codec='opus')
    #     sound.export(os.path.join(settings.MEDIA_ROOT, get_path(enc, 'upload1.wav')), format="wav")
    #
    #     combined += AudioSegment.from_wav(storage.open(os.path.join(settings.MEDIA_ROOT, get_path(enc, 'upload1.wav'))))
    #
    #     combined.export(os.path.join(settings.MEDIA_ROOT, get_path(enc, 'upload.wav')), format="wav")

    resp['success'] = True
    resp['msg'] = 'Saved'
    return ajax_response(resp)


def upload_audio_chunks_test(request):
    return render_to_response('encounters/test_audio.html')


@permissions_required(["add_encounter_timestamp"])
@login_required
@api_view(["POST"])
@timeit
def name_favorite(request, encounter_event_id):
    resp = {}
    name_favorite = request.POST.get("name_favorite", "")
    EncounterEvent.objects.filter(id=encounter_event_id).update(name_favorite=name_favorite)
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_encounter"])
@login_required
@api_view(["POST"])
@timeit
def delete_encounter(request, patient_id, encounter_id):
    Encounter.objects.get(id=encounter_id).delete()
    resp = {'success': True}
    return ajax_response(resp)


@login_required
@timeit
def increase_audio_played_count(request, encounter_id):
    resp = {}
    Encounter.objects.filter(id=encounter_id).update(audio_played_count=F('audio_played_count') + 1)
    resp['success'] = True
    return ajax_response(resp)


@login_required
@permissions_required(["add_encounter_timestamp"])
@api_view(["POST"])
@timeit
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
@timeit
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
