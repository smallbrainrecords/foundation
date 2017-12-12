# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0016_encounterproblemrecord'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='concept_id',
            field=models.CharField(max_length=20, null=True, blank=True),
        ),
    ]
