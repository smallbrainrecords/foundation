# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from emr.models import Problem, Observation, ObservationComponent, ObservationUnit, User, ObservationPinToProblem


def generate_glucose_for_diabetes_problem(apps, schema_editor):
    # Find all problem have concept id of 44054006
    diabetes_problems = Problem.objects.filter(concept_id="44054006")
    # Each problem patient find out whether or not Glucose data type exist. If not create one
    for problem in diabetes_problems:
        patient = User.objects.get(id=int(problem.patient_id))
        if not ObservationComponent.objects.filter(component_code="2345-7",
                                                   observation__subject=patient.profile).exists():
            # If patient doesn't have glucose data type yet then add new one
            observation = Observation.objects.create(subject=patient.profile, author=patient.profile, name="Glucose",
                                                     color="#FFD2D2", code="2345-7")
            observation.save()

            #  Add data unit
            observation_unit = ObservationUnit.objects.create(observation=observation, value_unit="mg/dL")
            observation_unit.is_used = True  # will be changed in future when having conversion
            observation_unit.save()

            #  Add data component
            observation_component = ObservationComponent.objects.create(observation=observation,
                                                                        component_code="2345-7", name="Glucose")
            observation_component.save()
        else:
            # if patient have glucose yet but doesn't being pined to the problem
            observation_component = ObservationComponent.objects.get(component_code="2345-7",
                                                                     observation__subject=patient.profile)
            observation = observation_component.observation

        # Pin glucose to the problem
        if not ObservationPinToProblem.objects.filter(observation=observation, problem=problem).exists():
            observation_pin_to_problem = ObservationPinToProblem.objects.create(author=patient.profile,
                                                                                observation=observation,
                                                                                problem=problem)
            observation_pin_to_problem.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0135_encounter_recorder_status'),
    ]

    operations = [
        migrations.RunPython(generate_glucose_for_diabetes_problem)
    ]
