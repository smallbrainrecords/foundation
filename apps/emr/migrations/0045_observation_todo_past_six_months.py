# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0044_observationcomponent_patient_refused_a1c'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='todo_past_six_months',
            field=models.BooleanField(default=False),
        ),
    ]
