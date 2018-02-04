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
from .models import Encounter, EncounterEvent, EncounterTodoRecord
from .models import EncounterProblemRecord


def op_add_event(physician, patient, event_summary, problem=None, todo=False):
    latest_encounter = Encounter.objects.filter(
        physician=physician,
        patient=patient).order_by('-id')

    if latest_encounter.exists():
        latest_encounter = latest_encounter[0]

        if latest_encounter.is_active():

            # Save Encounter Event
            encounter_event = EncounterEvent(
                encounter=latest_encounter,
                summary=event_summary)
            if not todo:
                encounter_event.save()

            # Add Problem Record if any
            if problem:
                try:
                    EncounterProblemRecord.objects.get(
                        encounter=latest_encounter, problem=problem)
                except EncounterProblemRecord.DoesNotExist:
                    EncounterProblemRecord.objects.create(
                        encounter=latest_encounter, problem=problem)

    return True


def op_add_todo_event(physician, patient, event_summary, todo=None, problem=False):
    latest_encounter = Encounter.objects.filter(
        physician=physician,
        patient=patient).order_by('-id')

    if latest_encounter.exists():
        latest_encounter = latest_encounter[0]

        if latest_encounter.is_active():

            # Save Encounter Event
            encounter_event = EncounterEvent(
                encounter=latest_encounter,
                summary=event_summary)
            if not problem:
                encounter_event.save()

            # Add Todo Record if any
            if todo:
                try:
                    EncounterTodoRecord.objects.get(
                        encounter=latest_encounter, todo=todo)
                except EncounterTodoRecord.DoesNotExist:
                    EncounterTodoRecord.objects.create(
                        encounter=latest_encounter, todo=todo)

    return True
