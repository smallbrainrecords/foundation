# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0022_auto_20160114_0912'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='start_time',
            field=models.TimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='problemsegment',
            name='start_time',
            field=models.TimeField(null=True, blank=True),
        ),
    ]
