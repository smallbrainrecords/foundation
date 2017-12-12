# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0065_commonproblem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='commonproblem',
            name='patient',
        ),
        migrations.AlterField(
            model_name='commonproblem',
            name='concept_id',
            field=models.CharField(max_length=20, unique=True, null=True, blank=True),
        ),
    ]
