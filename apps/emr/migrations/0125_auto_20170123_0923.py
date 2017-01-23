# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0124_auto_20170113_1517'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='todo',
            name='members',
        ),
        migrations.AddField(
            model_name='taggedtodoorder',
            name='status',
            field=models.IntegerField(default=0, choices=[(0, b'New'), (1, b'Viewed'), (2, b'Seen')]),
        ),
        migrations.AddField(
            model_name='todo',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='emr.TaggedToDoOrder'),
        ),
    ]
