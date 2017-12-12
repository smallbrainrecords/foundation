# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0005_auto_20150723_0942'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientController',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.BooleanField()),
                ('patient', models.ForeignKey(related_name='patient_physicians', to=settings.AUTH_USER_MODEL)),
                ('physician', models.ForeignKey(related_name='physician_patients', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
