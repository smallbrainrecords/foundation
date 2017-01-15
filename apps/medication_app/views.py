import reversion
from rest_framework.decorators import api_view

from common.views import *
from emr.models import Medication, MedicationTextNote, MedicationPinToProblem, ToDo, TaggedToDoOrder
from emr.mysnomedct import SnomedctConnector
from users_app.views import permissions_accessed
from .serializers import MedicationTextNoteSerializer, MedicationSerializer, MedicationPinToProblemSerializer


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
def get_medications(request, patient_id):
    resp = {'success': False}

    if permissions_accessed(request.user, int(patient_id)):
        medications = Medication.objects.filter(patient__user__id=patient_id)

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
        medication = Medication()
        medication.author = request.user.profile
        medication.patient = patient_user.profile
        medication.name = medication_name
        medication.concept_id = concept_id
        medication.search_str = search_string
        medication.save()

        resp['medication'] = MedicationSerializer(medication).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def add_medication_note(request, patient_id, medication_id):
    resp = {'success': False}
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

    resp = {'note': MedicationTextNoteSerializer(note).data, 'success': True}
    return ajax_response(resp)


@login_required
def delete_note(request, note_id):
    MedicationTextNote.objects.get(id=note_id).delete()
    resp = {'success': True}
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
            pin = MedicationPinToProblem(author=request.user.profile, medication_id=medication_id,
                                         problem_id=problem_id)
            pin.save()

        resp['pin'] = MedicationPinToProblemSerializer(pin).data
        resp['success'] = True

    return ajax_response(resp)


@login_required
@api_view(["POST"])
def change_active_medication(request, patient_id, medication_id):
    """
    Only nurse can change the active & inactive status
    https://trello.com/c/4qYulhv7
    :param request:
    :param patient_id:
    :param medication_id:
    :return:
    """
    resp = {'success': False}
    if request.user.profile.role == 'nurse':
        medication = Medication.objects.get(id=medication_id)
        medication.current = not medication.current
        medication.save()

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

    medication = Medication.objects.get(id=medication_id)

    old_medication_name = medication.name

    medication.name = json_body.get('name')  # 'name' is required request parameter
    medication.search_str = json_body.get('search_str')  # 'search_str' is required request parameter
    medication.concept_id = json_body.get('concept_id', None)

    comment = "{0} was changed to {1}".format(old_medication_name, medication.name)
    with reversion.create_revision():
        medication.save()
        reversion.set_user(request.user)
        reversion.set_comment(comment)

    # Refer: https://trello.com/c/W0rCwqtj
    # Create an todo related to this medication changing
    todo = ToDo()
    todo.todo = "Medication name changed from {0} to {1} by {2}".format(old_medication_name, medication.name,
                                                                        request.user.profile.__str__())
    todo.user = request.user
    todo.patient_id = patient_id
    todo.medication = medication
    todo.save()

    # Return data
    resp['medication'] = MedicationSerializer(medication).data
    resp['history'] = {'date': datetime.now().isoformat(), 'comment': comment}
    resp['success'] = True
    return ajax_response(resp)
