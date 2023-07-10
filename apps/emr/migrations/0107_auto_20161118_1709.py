# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0106_inrvalue_ispatient'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problem',
            name='inr',
        ),
        migrations.AddField(
            model_name='inr',
            name='problem',
            field=models.ForeignKey(related_name='problem_pin_inrs', blank=True, to='emr.Problem', null=True, on_delete=models.DO_NOTHING),
        ),
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
