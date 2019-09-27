# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

import emr.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0052_problemlabel_patient'),
    ]

    operations = [
        migrations.CreateModel(
            name='LabeledProblemList',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('problem_list', emr.models.ListField(null=True, blank=True)),
                ('labels', models.ManyToManyField(to='emr.ProblemLabel', blank=True)),
                ('patient',
                 models.ForeignKey(related_name='label_problem_list_patient', blank=True, to=settings.AUTH_USER_MODEL,
                                   null=True)),
                ('user',
                 models.ForeignKey(related_name='label_problem_list_user', blank=True, to=settings.AUTH_USER_MODEL,
                                   null=True)),
            ],
        ),
    ]
