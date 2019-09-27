# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0063_auto_20160626_0555'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemactivity',
            name='is_input_type',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='problemactivity',
            name='is_output_type',
            field=models.BooleanField(default=False),
        ),
    ]
