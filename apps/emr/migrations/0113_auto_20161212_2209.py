# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0112_auto_20161206_1027'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inr',
            name='target',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='inr_target',
            field=models.PositiveIntegerField(default=1, choices=[(1, b'2-3'), (0, b'2.5-3.5')]),
        ),
    ]
