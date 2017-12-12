# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0093_auto_20160920_1118'),
    ]

    operations = [
        migrations.AddField(
            model_name='todogroup',
            name='patient',
            field=models.ForeignKey(related_name='todo_group_patient', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
