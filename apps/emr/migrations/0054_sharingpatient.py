# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0053_labeledproblemlist'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharingPatient',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('shared', models.ForeignKey(related_name='patient_shared', to=settings.AUTH_USER_MODEL)),
                ('sharing', models.ForeignKey(related_name='patient_sharing', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
