# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations



def generate_glucose_for_diabetes_problem(apps, schema_editor):
    Problem = apps.get_model('emr', 'Problem')
    User = apps.get_model('auth', 'User')
    Observation = apps.get_model('emr', 'Observation')
    ObservationComponent = apps.get_model('emr', 'ObservationComponent')
    ObservationUnit = apps.get_model('emr', 'ObservationUnit')
    ObservationPinToProblem = apps.get_model('emr', 'ObservationPinToProblem')
    UserProfile = apps.get_model('emr', 'UserProfile')

    diabetes_problems = Problem.objects.filter(concept_id="44054006")
    for problem in diabetes_problems:
        try:
            patient = User.objects.get(id=int(problem.patient_id))
            profile = UserProfile.objects.filter(user_id=patient.id).first()
            if not profile:
                continue

            if not ObservationComponent.objects.filter(component_code="2345-7", observation__subject=profile).exists():
                observation = Observation.objects.create(subject=profile, author=profile, name="Glucose", color="#FFD2D2", code="2345-7")
                
                observation_unit = ObservationUnit.objects.create(observation=observation, value_unit="mg/dL")
                observation_unit.is_used = True
                observation_unit.save()

                observation_component = ObservationComponent.objects.create(observation=observation, component_code="2345-7", name="Glucose")
            else:
                observation_component = ObservationComponent.objects.filter(component_code="2345-7", observation__subject=profile).first()
                if not observation_component:
                    continue
                observation = observation_component.observation

            if not ObservationPinToProblem.objects.filter(observation=observation, problem=problem).exists():
                ObservationPinToProblem.objects.create(author=profile, observation=observation, problem=problem)
        except Exception:
            continue


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0135_encounter_recorder_status'),
    ]

    operations = [
        migrations.RunPython(generate_glucose_for_diabetes_problem)
    ]
