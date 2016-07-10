# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0045_observation_todo_past_six_months'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationComponentTextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, to='emr.UserProfile', null=True)),
                ('observation_component', models.ForeignKey(related_name='observation_component_notes', to='emr.ObservationComponent')),
            ],
        ),
    ]
