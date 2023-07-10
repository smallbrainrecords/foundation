# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0083_observationunit'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('observation', models.ForeignKey(related_name='observation_fields', to='emr.Observation', on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.AddField(
            model_name='observationcomponent',
            name='field',
            field=models.ForeignKey(related_name='observation_component_fields', blank=True, to='emr.ObservationField',
                                    null=True, on_delete=models.DO_NOTHING),
        ),
    ]
