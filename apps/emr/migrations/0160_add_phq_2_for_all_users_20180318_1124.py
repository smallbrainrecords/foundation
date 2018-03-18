# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from emr.models import Observation, ObservationComponent, User


def add_phq_2_for_all_users(apps, schema_editor):
    phq_2 = {
        'name': 'PHQ-2',
        'loinc_code': '55757-9',
        'color': '#FFFF00'
    }

    patients = User.objects.filter(profile__role='patient').all()
    for patient in patients:
        if not Observation.objects.filter(code=phq_2.get('name'), subject=patient).exists():
            observation = Observation.objects.create(name=phq_2.get('name'), color=phq_2.get('color'),
                                                     code=phq_2.get('loinc_code'), subject=patient)
            observation.save()

            #  Add data component
            observation_component = ObservationComponent.objects.create(observation=observation, name=phq_2.get('name'),
                                                                        component_code=phq_2.get('loinc_code'))
            observation_component.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0159_auto_20180312_0959'),
    ]

    operations = [
        migrations.RunPython(add_phq_2_for_all_users)
    ]
