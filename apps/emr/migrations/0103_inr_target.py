# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0102_auto_20161025_0156'),
    ]

    operations = [
        migrations.AddField(
            model_name='inr',
            name='target',
            field=models.BooleanField(default=True),
        ),
    ]
