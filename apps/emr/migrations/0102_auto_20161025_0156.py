# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0101_auto_20161024_2210'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inr',
            name='note',
        ),
        migrations.RemoveField(
            model_name='inr',
            name='pin',
        ),
        migrations.AddField(
            model_name='inr',
            name='observation',
            field=models.ForeignKey(related_name='observation_pin_inrs', blank=True, to='emr.Observation', null=True),
        ),
        migrations.AddField(
            model_name='inr',
            name='problem',
            field=models.ForeignKey(related_name='problem_pin_inrs', blank=True, to='emr.Problem', null=True),
        ),
    ]
