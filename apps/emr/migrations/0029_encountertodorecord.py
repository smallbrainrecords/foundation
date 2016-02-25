# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0028_auto_20160218_0200'),
    ]

    operations = [
        migrations.CreateModel(
            name='EncounterTodoRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('encounter', models.ForeignKey(related_name='encounter_todo_records', to='emr.Encounter')),
                ('todo', models.ForeignKey(related_name='todo_encounter_records', to='emr.ToDo')),
            ],
        ),
    ]
