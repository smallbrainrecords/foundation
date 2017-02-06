from datetime import datetime, timedelta

from django.db import models


class AOneCManager(models.Manager):
    def create_if_not_exist(self, problem):
        from emr.models import AOneC, Observation, ObservationComponent, OBSERVATION_TYPES
        if not Observation.objects.filter(subject=problem.patient.profile, name=OBSERVATION_TYPES[0]['name']).exists():
            observation = Observation.objects.create(subject=problem.patient.profile,
                                                     name=OBSERVATION_TYPES[0]['name'])

            observation.save()
        else:
            observation = Observation.objects.get(subject=problem.patient.profile, name=OBSERVATION_TYPES[0]['name'])

        if not ObservationComponent.objects.filter(observation=observation, name=OBSERVATION_TYPES[0]['name']).exists():
            observation_component = ObservationComponent()
            observation_component.observation = observation
            observation_component.name = OBSERVATION_TYPES[0]['name']
            observation_component.save()

        if not AOneC.objects.filter(problem=problem).exists():
            AOneC.objects.create(problem=problem, observation=observation)


class ProblemManager(models.Manager):
    def create_new_problem(self, patient_id, problem_name, concept_id, user_profile):
        from emr.models import Problem, Observation, AOneC, OBSERVATION_TYPES
        new_problem = Problem(patient_id=patient_id, problem_name=problem_name, concept_id=concept_id)
        if user_profile.role in ('physician', 'admin'):
            new_problem.authenticated = True
        new_problem.save()
        # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
        if concept_id in ['73211009', '46635009', '44054006']:
            observation = Observation.objects.create(name=OBSERVATION_TYPES[0]['name'],
                                                     subject=new_problem.patient.profile)
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
        from emr.models import EncounterEvent, ObservationValue, EncounterObservationValue

        latest_encounter = self.get(physician=physician, id=encounter_id)
        latest_encounter.stoptime = datetime.now()
        latest_encounter.save()

        event_summary = 'Stopped encounter by <b>%s</b>' % physician.username
        EncounterEvent.objects.create(encounter=latest_encounter, summary=event_summary)

        # https://trello.com/c/cFylaLdv
        data_value = ObservationValue.objects.filter(
            component__observation__subject=latest_encounter.patient.profile).filter(
            created_on__lte=latest_encounter.stoptime).filter(created_on__gte=datetime.now().date()).all()
        for value in data_value:
            EncounterObservationValue.objects.create(encounter=latest_encounter, observation_value=value)

    def create_new_encounter(self, patient_id, physician):
        from emr.models import EncounterEvent
        from emr.models import Encounter



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
        from django.db.models import Max
        order = self.filter(patient=patient).aggregate(Max('order'))
        if not order['order__max']:
            order = 1
        else:
            order = order['order__max'] + 1
        new_todo = self.create(patient=patient, todo=todo_name, due_date=due_date, order=order)
        return new_todo

    def add_staff_todo(self, user_id, todo_name, due_date):
        from django.db.models import Max
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
            ColonCancerScreening.objects.create(problem=problem, patient=problem.patient.profile)


class ColonCancerStudyManager(models.Manager):
    def create_new_study(self, colon_cancer):
        self.create(colon=colon_cancer, patient=colon_cancer.problem.patient.profile)
