# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0118_auto_20170103_1104'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_access_tagged_todo',
            field=models.DateTimeField(default=datetime.datetime(2017, 1, 10, 20, 49, 41, 454000)),
        ),
    ]
