# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0042_auto_20160414_0305'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationcomponent',
            name='effective_datetime',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
