# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0115_auto_20161213_1459'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inrvalue',
            name='author',
        ),
        migrations.RemoveField(
            model_name='inrvalue',
            name='inr',
        ),
        migrations.RemoveField(
            model_name='inr',
            name='observation',
        ),
        migrations.RemoveField(
            model_name='inr',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='inr',
            name='problem',
        ),
        migrations.AddField(
            model_name='inr',
            name='current_dose',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inr',
            name='new_dosage',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inr',
            name='next_inr',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inr',
            name='observation_value',
            field=models.OneToOneField(null=True, to='emr.ObservationValue'),
        ),
        migrations.AlterField(
            model_name='inr',
            name='author',
            field=models.ForeignKey(related_name='author_inr', blank=True, to='emr.UserProfile', null=True),
        ),
        migrations.DeleteModel(
            name='InrValue',
        ),
    ]
