# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0126_auto_20170125_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='encounter',
            name='audio_played_count',
            field=models.IntegerField(default=0),
        ),
    ]
