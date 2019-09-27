# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0043_observationcomponent_effective_datetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationcomponent',
            name='patient_refused_A1C',
            field=models.BooleanField(default=False),
        ),
    ]
