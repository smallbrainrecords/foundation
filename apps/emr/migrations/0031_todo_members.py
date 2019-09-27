# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0030_todoactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='members',
            field=models.ManyToManyField(to='emr.UserProfile', blank=True),
        ),
    ]
