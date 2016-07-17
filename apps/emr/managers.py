from django.db import models

class ObservationManager(models.Manager):
    def create_if_not_exist(self, problem):
        from apps.emr.models import Observation
        if not Observation.objects.filter(problem=problem).exists():
            observation = Observation.objects.create(problem=problem, subject=problem.patient.profile)
