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

from datetime import datetime, timedelta

from django.db import models
from django.db.models import Max


class AOneCManager(models.Manager):
    def create_if_not_exist(self, problem):
        from emr.models import Observation, ObservationComponent, AOneC
        a1c = {
            'name': 'a1c',
            'loinc_code': '4548-4',
        }

        if not Observation.objects.filter(subject=problem.patient, name=a1c.get('name')).exists():
            observation = Observation.objects.create(subject=problem.patient, name=a1c.get('name'),
                                                     code=a1c.get('loinc_code'))

            observation.save()
        else:
            observation = Observation.objects.get(subject=problem.patient, name=a1c.get('name'))

        if not ObservationComponent.objects.filter(observation=observation, name=a1c.get('name')).exists():
            observation_component = ObservationComponent()
            observation_component.observation = observation
            observation_component.component_code = a1c.get('loinc_code')
            observation_component.name = a1c.get('name')
            observation_component.save()

        if not AOneC.objects.filter(problem=problem).exists():
            AOneC.objects.create(problem=problem, observation=observation)


class ProblemManager(models.Manager):
    def create_new_problem(self, patient_id, problem_name, concept_id, user_profile):
        from emr.models import Problem
        from emr.models import Observation
        from emr.models import AOneC

        a1c = {
            'name': 'a1c',
            'loinc_code': '4548-4',
        }

        new_problem = Problem(patient_id=patient_id, problem_name=problem_name, concept_id=concept_id)
        if user_profile.role in ('physician', 'admin'):
            new_problem.authenticated = True
        new_problem.save()

        # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
        if concept_id in ['73211009', '46635009', '44054006']:
            observation = Observation.objects.create(name=a1c.get('name'), code=a1c.get('loinc_code'),
                                                     subject=new_problem.patient)
            AOneC.objects.create(problem=new_problem, observation=observation)
        return new_problem


class ProblemNoteManager(models.Manager):
    def create_history_note(self, author, problem, note):
        from emr.models import ProblemNote
        return ProblemNote.objects.create(author=author, problem=problem, note=note, note_type='history')

    def create_wiki_note(self, author, problem, note):
        from emr.models import ProblemNote
        return ProblemNote.objects.create(author=author, problem=problem, note=note, note_type='wiki')


class EncounterManager(models.Manager):
    def stop_patient_encounter(self, physician, encounter_id):
        from emr.models import EncounterEvent
        from emr.models import EncounterObservationValue
        from emr.models import ObservationValue

        latest_encounter = self.get(physician=physician, id=encounter_id)
        latest_encounter.stoptime = datetime.now()
        latest_encounter.recorder_status = 2
        latest_encounter.save()

        event_summary = 'Stopped encounter by <b>%s</b>' % physician.username
        EncounterEvent.objects.create(encounter=latest_encounter, summary=event_summary)

        # https://trello.com/c/cFylaLdv
        data_value = ObservationValue.objects.filter(
            component__observation__subject=latest_encounter.patient).filter(
            created_on__lte=latest_encounter.stoptime).filter(created_on__gte=datetime.now().date()).all()
        for value in data_value:
            EncounterObservationValue.objects.create(encounter=latest_encounter, observation_value=value)

    def create_new_encounter(self, patient_id, physician):
        from emr.models import EncounterEvent
        # encounter = self.create(patient_id=patient_id, physician=physician, recorder_status=0)
        encounter = self.create(patient_id=patient_id, physician=physician)
        # Add event started encounter
        event_summary = 'Started encounter by <b>%s</b>' % (physician.username)
        EncounterEvent.objects.create(encounter=encounter, summary=event_summary)
        return encounter

    def add_event_summary(self, encounter_id, physician, event_summary):
        from emr.models import EncounterEvent
        latest_encounter = self.get(physician=physician, id=encounter_id)
        encounter_event = EncounterEvent.objects.create(encounter=latest_encounter, summary=event_summary)
        return encounter_event

    def add_timestamp(self, encounter_id, added_by, timestamp):
        from emr.models import EncounterEvent
        encounter = self.get(id=encounter_id)

        timestamp = encounter.starttime + timedelta(seconds=timestamp)
        summary = 'A timestamp added by <b>' + added_by.username + '</b>'
        encounter_event = EncounterEvent.objects.create(encounter=encounter, timestamp=timestamp, summary=summary)
        return encounter_event


class TodoManager(models.Manager):
    def add_patient_todo(self, patient, todo_name, due_date):

        order = self.filter(patient=patient).aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        new_todo = self.create(patient=patient, todo=todo_name, due_date=due_date, order=order)
        return new_todo

    def add_staff_todo(self, user_id, todo_name, due_date):

        order = self.filter(user_id=user_id).aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        new_todo = self.create(user_id=user_id, todo=todo_name, due_date=due_date, order=order)
        return new_todo


class ColonCancerScreeningManager(models.Manager):
    def create_if_not_exist(self, problem):
        from emr.models import ColonCancerScreening
        if not ColonCancerScreening.objects.filter(problem=problem).exists():
            ColonCancerScreening.objects.create(problem=problem, patient=problem.patient)


class ColonCancerStudyManager(models.Manager):
    def create_new_study(self, colon_cancer):
        self.create(colon=colon_cancer, patient=colon_cancer.problem.patient.profile)
