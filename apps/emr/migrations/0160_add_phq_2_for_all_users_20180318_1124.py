# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def add_phq_2_for_all_users(apps, schema_editor):
    # Historical models, NOT live imports (fixed 2026-07-11) — see the
    # matching note in 0141: live-model queries here break every fresh-DB
    # build once the live model gains a column the table lacks at this
    # point in the chain. Prod applied this in 2018; behavior identical.
    Observation = apps.get_model('emr', 'Observation')
    ObservationComponent = apps.get_model('emr', 'ObservationComponent')
    User = apps.get_model('auth', 'User')

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
