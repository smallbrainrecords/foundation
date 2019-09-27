# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

import emr.models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0061_encounterevent_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='labeledtodolist',
            name='expanded',
            field=emr.models.ListField(null=True, blank=True),
        ),
    ]
