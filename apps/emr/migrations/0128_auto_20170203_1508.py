# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0127_encounter_audio_played_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='EncounterObservationValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('encounter', models.ForeignKey(to='emr.Encounter', on_delete=models.DO_NOTHING)),
                ('observation_value', models.ForeignKey(to='emr.ObservationValue', on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.AddField(
            model_name='encounter',
            name='encounter_document',
            field=models.ManyToManyField(to='emr.ObservationValue', through='emr.EncounterObservationValue'),
        ),
    ]
