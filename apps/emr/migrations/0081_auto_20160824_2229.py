# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import emr.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0080_auto_20160823_0244'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', emr.models.ListField(null=True, blank=True)),
                ('patient', models.ForeignKey(related_name='patient_observation_order', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='user_observation_order', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='observation',
            name='color',
            field=models.CharField(max_length=7, null=True, blank=True),
        ),
    ]
