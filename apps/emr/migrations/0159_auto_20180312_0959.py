# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0158_auto_20171118_2343'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='insurance_medicare',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='insurance_note',
            field=models.TextField(blank=True),
        ),
    ]
