# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0038_auto_20160320_2319'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='label',
            name='user',
        ),
    ]
