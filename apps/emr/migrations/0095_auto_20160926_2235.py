# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0094_todogroup_patient'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todo',
            name='group',
            field=models.ForeignKey(related_name='items', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='emr.ToDoGroup', null=True),
        ),
    ]
