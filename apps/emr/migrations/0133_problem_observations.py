# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0132_document_document_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='observations',
            field=models.ManyToManyField(to='emr.Observation', through='emr.ObservationPinToProblem'),
        ),
    ]
