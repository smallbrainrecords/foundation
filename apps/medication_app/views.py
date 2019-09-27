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
import reversion
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from rest_framework.decorators import api_view

from common.views import *
from emr.models import Medication, MedicationTextNote, MedicationPinToProblem, ToDo, TodoActivity, VWMedications
from emr.mysnomedct import VWMedicationsSerializers
from emr.operations import op_add_todo_event
from medication_app.operations import op_medication_event, op_pin_medication_to_problem_for_all_controlled_patient, \
    count_pinned_have_same_medication_concept_id_and_problem_concept_id
from users_app.views import permissions_accessed
from .serializers import MedicationTextNoteSerializer, MedicationSerializer, MedicationPinToProblemSerializer


@login_required
def list_terms(request):
    # We list snomed given a query
    query = request.GET['query']
    result = VWMedications.objects.using('snomedict').filter(term__contains="{0}".format(query)).all()
    results_holder = VWMedicationsSerializers(result, many=True).data
    return ajax_response(results_holder)


@login_required
def get_medications(request, patient_id):
    """

    :param request:
    :param patient_id: Patient user id
    :return:
    """
    resp = {'success': False}

    if permissions_accessed(request.user, int(patient_id)):
        medications = Medication.objects.filter(patient__id=patient_id).order_by('name')

        resp['success'] = True
        resp['info'] = MedicationSerializer(medications, many=True).data
    return ajax_response(resp)


@login_required
def get_medication(request, patient_id, medication_id):
    resp = {'success': False}
    history_list = []

    if permissions_accessed(request.user, int(patient_id)):
        try:
            medication = Medication.objects.get(id=medication_id)
            reversion_list = reversion.get_for_object(medication)
            for item in reversion_list:
                history_list.append({
                    'date': item.revision.date_created.isoformat(),
                    'comment': item.revision.comment
                })
            notes = MedicationTextNote.objects.filter(medication_id=medication_id).order_by('-datetime')
        except Medication.DoesNotExist:
            pass

        resp['success'] = True
        resp['info'] = MedicationSerializer(medication).data
        resp['history'] = history_list
        resp['noteHistory'] = MedicationTextNoteSerializer(notes, many=True).data

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_medication(request, patient_id):
    resp = {'success': False}

    medication_name = request.POST.get("name")
    concept_id = request.POST.get("concept_id", "")
    search_string = request.POST.get("search_str", "")
    patient_user = User.objects.get(id=patient_id)

    if permissions_accessed(request.user, int(patient_id)) and medication_name:
        medication = Medication(author=request.user, patient=patient_user, name=medication_name, concept_id=concept_id,
                                search_str=search_string)
        medication.save()

        op_medication_event(medication, request.user, patient_user,
                            "Added medication <a href='#/medication/{0}'><b>{1}</b></a>".format(medication.id,
                                                                                                medication_name))
        resp['medication'] = MedicationSerializer(medication).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_medication_note(request, patient_id, medication_id):
    resp = {'success': False}
    note = request.POST.get("note", None)
    old_note = request.POST.get("old_note", None)
    patient_user = User.objects.get(id=patient_id)

    if permissions_accessed(request.user, int(patient_id)):
        medication = Medication.objects.get(id=medication_id)
        latest_note = medication.medication_notes.last()

        note = MedicationTextNote(author=request.user, note=note, medication=medication)
        note.save()

        op_medication_event(medication, request.user, patient_user,
                            "<b>{0}</b> was changed from <b>{1}</b> to <b>{2}</b>".format(medication, latest_note,
                                                                                          note))

        resp['note'] = MedicationTextNoteSerializer(note).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
def edit_note(request, note_id):
    resp = {'success': False}

    note = MedicationTextNote.objects.get(id=note_id)
    if note.author == request.user:
        note.note = request.POST.get('note')
        note.save()
        resp['note'] = MedicationTextNoteSerializer(note).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
def delete_note(request, note_id):
    resp = {'success': False}
    note = MedicationTextNote.objects.get(id=note_id)
    if note.author == request.user:
        note.delete()
        resp['success'] = True

    return ajax_response(resp)


@login_required
def get_pins(request, medication_id):
    pins = MedicationPinToProblem.objects.filter(medication_id=medication_id)
    resp = {'success': True, 'pins': MedicationPinToProblemSerializer(pins, many=True).data}
    return ajax_response(resp)


@login_required
@api_view(["POST"])
def pin_to_problem(request, patient_id):
    resp = {'success': False}
    if permissions_accessed(request.user, int(patient_id)):
        medication_id = request.POST.get("medication_id", None)
        problem_id = request.POST.get("problem_id", None)

        try:
            pin = MedicationPinToProblem.objects.get(medication_id=medication_id, problem_id=problem_id)
            pin.delete()
        except MedicationPinToProblem.DoesNotExist:
            pin = MedicationPinToProblem(author=request.user, medication_id=medication_id, problem_id=problem_id)
            pin.save()

            pinned_instance_set, count = count_pinned_have_same_medication_concept_id_and_problem_concept_id(
                request.user, pin.medication, pin.problem)
            if request.user.profile.role == "physician" and count >= 3:
                op_pin_medication_to_problem_for_all_controlled_patient(request.user, pinned_instance_set,
                                                                        pin.medication, pin.problem)
        resp['pin'] = MedicationPinToProblemSerializer(pin).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def change_active_medication(request, patient_id, medication_id):
    """
    :param request:
    :param patient_id:
    :param medication_id:
    :return:
    """
    resp = {'success': False}
    patient_user = User.objects.get(id=patient_id)

    medication = Medication.objects.get(id=medication_id)
    medication.current = not medication.current
    medication.save()

    op_medication_event(medication, request.user, patient_user,
                        "<b>{0}</b> changed to <b>{1}</b>".format(medication.name,
                                                                  medication.current and "active" or "inactive"))
    resp['medication'] = MedicationSerializer(medication).data
    resp['success'] = True

    return ajax_response(resp)


@login_required
def change_dosage(request, patient_id, medication_id):
    """
    Change dosage in medication detail page
    :param medication_id:
    :param patient_id:
    :param request:
    :return:
    """
    resp = {'success': False}
    json_body = json.loads(request.body)
    name = json_body.get('name')
    search_string = json_body.get('search_str')
    concept_id = json_body.get('concept_id', None)
    patient_user = User.objects.get(id=patient_id)

    medication = Medication.objects.get(id=medication_id)
    old_medication_name = medication.name
    medication.name = name
    medication.search_str = search_string
    medication.concept_id = concept_id

    comment = "{0} was changed to {1}".format(old_medication_name, medication.name)
    with reversion.create_revision():
        medication.save()
        reversion.set_user(request.user)
        reversion.set_comment(comment)

    op_medication_event(medication, request.user, patient_user,
                        "Medication name changed from <b>{0}</b> to <b>{1}</b>".format(old_medication_name,
                                                                                       medication.name))

    # Create an todo related to this medication changing
    todo = ToDo(todo="Medication name changed from {0} to {1}".format(old_medication_name, medication.name),
                user=request.user, patient_id=patient_id, medication=medication)
    todo.save()

    op_add_todo_event(request.user, patient_user,
                      "Added todo <a href='#/todo/{0}'><b>{1}</b></a>".format(todo.id, todo.todo))

    TodoActivity(todo=todo, author=request.user, activity="Added this todo.").save()

    # Return data
    resp['medication'] = MedicationSerializer(medication).data
    resp['history'] = {'date': datetime.now().isoformat(), 'comment': comment}
    resp['success'] = True
    return ajax_response(resp)
