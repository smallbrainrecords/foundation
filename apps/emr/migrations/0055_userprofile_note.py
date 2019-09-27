# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0054_sharingpatient'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='note',
            field=models.TextField(null=True, blank=True),
        ),
    ]
