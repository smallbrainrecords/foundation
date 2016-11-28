# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0106_inrvalue_ispatient'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inrvalue',
            name='effective_datetime',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='inrvalue',
            name='next_inr',
            field=models.DateField(null=True, blank=True),
        ),
    ]
