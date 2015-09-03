# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0009_physicianteam'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patientcontroller',
            name='author',
            field=models.BooleanField(default=False),
        ),
    ]
