from datetime import datetime
from django.utils import timezone
from django.db import models

#def RepresentsInt(times):
#    for t in times:
#        try:
#            int(t)
#        except ValueError:
#            return False
#
#    return True

class ObservationManager(models.Manager):
    def create_if_not_exist(self, problem):
        from apps.emr.models import Observation
        if not Observation.objects.filter(problem=problem).exists():
            Observation.objects.create(problem=problem, subject=problem.patient.profile)

class ProblemManager(models.Manager):
    def create_new_problem(self, patient_id, problem_name, concept_id, user_profile):
        from apps.emr.models import Problem, Observation
        new_problem = Problem(patient__id=patient_id, problem_name=problem_name, concept_id=concept_id)
        if user_profile.role in ('physician', 'admin'):
            new_problem.authenticated = True
        new_problem.save()
        # add a1c widget to problems that have concept id 73211009, 46635009, 44054006
        if concept_id in ['73211009', '46635009', '44054006']:
            Observation.objects.create(problem=new_problem, subject=new_problem.patient.profile)
        return new_problem

class ProblemNoteManager(models.Manager):
    def create_history_note(self, author, problem, note):
        from apps.emr.models import ProblemNote
        return ProblemNote.objects.create(author=author, problem=problem, note=note, note_type='history')

    def create_wiki_note(self, author, problem, note):
        from apps.emr.models import ProblemNote
        return ProblemNote.objects.create(author=author, problem=problem, note=note, note_type='wiki')

class EncounterManager(models.Manager):
    def stop_patient_encounter(self, physician, encounter_id):
        from apps.emr.models import EncounterEvent
        latest_encounter = self.get(physician=physician, id=encounter_id)
        latest_encounter.stoptime = datetime.now()
        latest_encounter.save()

        event_summary = 'Stopped encounter by <b>%s</b>' % physician.username
        EncounterEvent.objects.create(encounter=latest_encounter, summary=event_summary)

    def create_new_encounter(self, patient_id, physician):
        from apps.emr.models import EncounterEvent
        encounter = self.create(patient_id=patient_id, physician=physician)
        # Add event started encounter
        event_summary = 'Started encounter by <b>%s</b>' % (physician.username)
        encounter_event = EncounterEvent.objects.create(encounter=encounter, summary=event_summary)
        return encounter

    def add_event_summary(self, encounter_id, physician, event_summary):
        from apps.emr.models import EncounterEvent
        latest_encounter = self.get(physician=physician, id=encounter_id)
        encounter_event = EncounterEvent.objects.create(encounter=latest_encounter, summary=event_summary)
        return encounter_event

    def add_timestamp(self, encounter_id, added_by):
        from apps.emr.models import EncounterEvent
        encounter = self.get(id=encounter_id)
        timestamp = timezone.now()
        # timestamp = request.POST.get('timestamp', '')
        # times = timestamp.split(":")
        # if RepresentsInt(times):
        #     if len(times) == 3:
        #         plustime = timedelta(hours=int(times[0]), minutes=int(times[1]), seconds=int(times[2]))
        #     elif len(times) == 2:
        #         plustime = timedelta(minutes=int(times[0]), seconds=int(times[1]))
        #     elif len(times) == 1:
        #         plustime = timedelta(seconds=int(times[0]))
        #     else:
        #         plustime = timedelta(seconds=0)

        #     timestamp = encounter.starttime + plustime
        summary = 'A timestamp added by <b>' + added_by.username + '</b>'
        encounter_event = EncounterEvent.objects.create(encounter=encounter, timestamp=timestamp, summary=summary)
        return encounter_event

