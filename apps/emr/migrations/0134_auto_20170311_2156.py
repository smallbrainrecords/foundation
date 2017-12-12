# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from emr.models import ObservationComponent, ObservationUnit


def change_default_height_unit(apps, schema_editor):
    observation_component = ObservationComponent.objects.filter(component_code='8302-2').all()

    for component in observation_component:
        unit_set = component.observation.observation_units.all()
        for unit in unit_set:
            unit.is_used = False
            unit.save()
        if ObservationUnit.objects.filter(observation=component.observation, value_unit='in').exists():
            unit = ObservationUnit.objects.filter(observation=component.observation, value_unit='in').get()
            unit.is_used = True
            unit.save()
        else:
            ObservationUnit.objects.create(observation=component.observation, value_unit='in', is_used=True)


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0133_problem_observations'),
    ]

    operations = [
        migrations.RunPython(change_default_height_unit)
    ]
