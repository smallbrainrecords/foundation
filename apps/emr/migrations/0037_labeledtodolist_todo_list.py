# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import emr.models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0036_labeledtodolist'),
    ]

    operations = [
        migrations.AddField(
            model_name='labeledtodolist',
            name='todo_list',
            field=emr.models.ListField(null=True, blank=True),
        ),
    ]
