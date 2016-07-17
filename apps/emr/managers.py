from django.db import models

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
