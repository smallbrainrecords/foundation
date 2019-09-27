# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0015_auto_20151014_0651'),
    ]

    operations = [
        migrations.CreateModel(
            name='EncounterProblemRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('encounter', models.ForeignKey(related_name='encounter_problem_records', to='emr.Encounter')),
                ('problem', models.ForeignKey(related_name='problem_encounter_records', to='emr.Problem')),
            ],
        ),
    ]
