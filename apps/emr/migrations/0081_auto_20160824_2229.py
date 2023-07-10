# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import emr.models
from django.conf import settings
from django.db import migrations, models


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
                ('patient',
                 models.ForeignKey(related_name='patient_observation_order', blank=True, to=settings.AUTH_USER_MODEL,
                                   null=True, on_delete=models.DO_NOTHING)),
                ('user',
                 models.ForeignKey(related_name='user_observation_order', blank=True, to=settings.AUTH_USER_MODEL,
                                   null=True, on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.AddField(
            model_name='observation',
            name='color',
            field=models.CharField(max_length=7, null=True, blank=True),
        ),
    ]
