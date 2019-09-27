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
from django.contrib.auth.decorators import login_required

from common.views import *
from data_app.serializers import ObservationValueTextNoteSerializer, ObservationValueSerializer
from emr.models import AOneCTextNote, ObservationComponent, UserProfile, ObservationValueTextNote, \
    AOneC, ObservationValue
from emr.operations import op_add_event
from problems_app.operations import add_problem_activity
from .serializers import AOneCTextNoteSerializer, AOneCSerializer


# set problem authentication to false if not physician, admin
def set_problem_authentication_false(actor_profile, problem):
    role = actor_profile.role
    authenticated = role in ["physician", "admin"]
    problem.authenticated = authenticated
    problem.save()


@login_required
def track_a1c_click(request, a1c_id):
    actor = request.user
    a1c_info = AOneC.objects.get(id=a1c_id)
    patient = a1c_info.problem.patient

    summary = "<b>%s</b> visited <u>a1c</u> module" % (actor.username)
    op_add_event(actor, patient, summary, a1c_info.problem)

    resp = {}
    return ajax_response(resp)


@login_required
def get_a1c_info(request, a1c_id):
    a1c_info = AOneC.objects.get(id=a1c_id)
    resp = {}
    resp['success'] = True
    resp['info'] = AOneCSerializer(a1c_info).data
    return ajax_response(resp)


# Note
@permissions_required(["add_a1c_note"])
@login_required
def add_note(request, a1c_id):
    resp = {}
    note = request.POST.get("note")

    a1c_note = AOneCTextNote.objects.create(a1c_id=a1c_id, author=request.user, note=note)

    resp['success'] = True
    resp['note'] = AOneCTextNoteSerializer(a1c_note).data
    return ajax_response(resp)


@permissions_required(["edit_a1c_note"])
@login_required
def edit_note(request, note_id):
    resp = {}

    note = AOneCTextNote.objects.get(id=note_id)
    note.note = request.POST.get('note')
    note.save()

    resp['note'] = AOneCTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_a1c_note"])
@login_required
def delete_note(request, note_id):
    resp = {}

    AOneCTextNote.objects.get(id=note_id).delete()

    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["add_a1c"])
@login_required
def patient_refused(request, a1c_id):
    a1c = AOneC.objects.get(id=a1c_id)
    observation = a1c.observation
    observation.effective_datetime = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()
    observation.save()
    if request.POST.get('patient_refused_A1C', None):
        a1c.patient_refused_A1C = True

    a1c.save()
    # set problem authentication
    actor_profile = UserProfile.objects.get(user=request.user)
    set_problem_authentication_false(actor_profile, a1c.problem)

    summary = """
        Patient refused a1c ,
        <u>problem</u> <b>%s</b>
        """ % (a1c.problem.problem_name)

    add_problem_activity(a1c.problem, request.user, summary)

    resp = {}
    resp['a1c'] = AOneCSerializer(a1c).data
    resp['success'] = True
    return ajax_response(resp)


# Value
@permissions_required(["add_a1c"])
@login_required
def add_value(request, component_id):
    resp = {}
    actor_profile = UserProfile.objects.get(user=request.user)
    component = ObservationComponent.objects.get(id=component_id)
    effective_date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d').date()

    value = ObservationValue.objects.create(component=component,
                                            value_quantity=request.POST.get("value", None),
                                            effective_datetime=effective_date,
                                            author=request.user)

    a1c = component.observation.observation_aonecs
    a1c.patient_refused_A1C = False
    a1c.todo_past_six_months = False
    a1c.save()

    resp['value'] = ObservationValueSerializer(value).data
    resp['success'] = True

    # set problem authentication
    set_problem_authentication_false(actor_profile, a1c.problem)

    summary = """
        Added new a1c value <u>A1C</u> : <b>%s</b> ,
        <u>problem</u> <b>%s</b>
        """ % (value.value_quantity, a1c.problem.problem_name)

    add_problem_activity(a1c.problem, request.user, summary)

    summary = "An A1C value of <b>%s</b> was entered" % (value.value_quantity)
    op_add_event(request.user, a1c.problem.patient, summary, a1c.problem)
    return ajax_response(resp)


@permissions_required(["delete_observation_component"])
@login_required
def delete_value(request, value_id):
    resp = {}
    ObservationValue.objects.get(id=value_id).delete()
    resp['success'] = True
    return ajax_response(resp)


@login_required
def get_observation_value_info(request, value_id):
    resp = {}

    observation_value_info = ObservationValue.objects.get(id=value_id)

    resp['success'] = True
    resp['info'] = ObservationValueSerializer(observation_value_info).data
    resp['a1c_id'] = observation_value_info.component.observation.observation_aonecs.id

    return ajax_response(resp)


@permissions_required(["edit_observation_component"])
@login_required
def edit_value(request, value_id):
    resp = {}

    value = ObservationValue.objects.get(id=value_id)
    value.value_quantity = request.POST.get('value_quantity')
    value.effective_datetime = datetime.strptime(request.POST.get('effective_datetime'), '%Y-%m-%d').date()
    value.save()

    resp['success'] = True
    resp['info'] = ObservationValueSerializer(value).data

    return ajax_response(resp)


# Value Note
@permissions_required(["add_a1c_note"])
@login_required
def add_value_note(request, value_id):
    resp = {}

    note = request.POST.get("note")
    note = ObservationValueTextNote.objects.create(observation_value_id=value_id, author=request.user, note=note)

    resp['note'] = ObservationValueTextNoteSerializer(note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["edit_a1c_note"])
@login_required
def edit_value_note(request, note_id):
    resp = {}
    note = request.POST.get('note')

    observation_value_text_note = ObservationValueTextNote.objects.get(id=note_id)
    observation_value_text_note.note = note
    observation_value_text_note.save()

    resp['note'] = ObservationValueTextNoteSerializer(observation_value_text_note).data
    resp['success'] = True
    return ajax_response(resp)


@permissions_required(["delete_a1c_note"])
@login_required
def delete_value_note(request, note_id):
    resp = {}

    ObservationValueTextNote.objects.get(id=note_id).delete()

    resp['success'] = True
    return ajax_response(resp)
