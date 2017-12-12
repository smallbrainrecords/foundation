# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0041_observation_problem'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationTextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, to='emr.UserProfile', null=True)),
                ('observation', models.ForeignKey(related_name='observation_notes', to='emr.Observation')),
            ],
        ),
        migrations.AddField(
            model_name='todo',
            name='observation',
            field=models.ForeignKey(related_name='observation_todos', blank=True, to='emr.Observation', null=True),
        ),
    ]
