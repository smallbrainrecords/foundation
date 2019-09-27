# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0134_auto_20170311_2156'),
    ]

    operations = [
        migrations.AddField(
            model_name='encounter',
            name='recorder_status',
            field=models.IntegerField(default=0, choices=[(0, b'isRecording'), (1, b'isPaused'), (2, b'isStopped')]),
        ),
    ]
