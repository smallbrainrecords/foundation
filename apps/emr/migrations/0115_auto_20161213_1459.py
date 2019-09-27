# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0114_auto_20161213_0932'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='todo',
            name='inr',
        ),
        migrations.AddField(
            model_name='todo',
            name='created_at',
            field=models.PositiveIntegerField(default=0, choices=[(0, b''), (1, b'inr_widget')]),
        ),
    ]
