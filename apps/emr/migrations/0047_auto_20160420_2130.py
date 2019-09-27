# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0046_observationcomponenttextnote'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='observationcomponent',
            options={'ordering': ['effective_datetime']},
        ),
        migrations.RemoveField(
            model_name='observationcomponent',
            name='patient_refused_A1C',
        ),
        migrations.AddField(
            model_name='observation',
            name='patient_refused_A1C',
            field=models.BooleanField(default=False),
        ),
    ]
