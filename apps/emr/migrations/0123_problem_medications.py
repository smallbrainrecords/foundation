# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0122_todo_medication'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='medications',
            field=models.ManyToManyField(to='emr.Medication', through='emr.MedicationPinToProblem'),
        ),
    ]
