# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0105_auto_20161107_0102'),
    ]

    operations = [
        migrations.AddField(
            model_name='inrvalue',
            name='ispatient',
            field=models.BooleanField(default=False),
        ),
    ]
