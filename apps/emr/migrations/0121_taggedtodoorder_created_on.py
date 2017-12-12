# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0120_auto_20170111_0132'),
    ]

    operations = [
        migrations.AddField(
            model_name='taggedtodoorder',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
