# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0097_auto_20160930_0441'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='todogroup',
            name='patient',
        ),
        migrations.RemoveField(
            model_name='todo',
            name='group',
        ),
        migrations.RemoveField(
            model_name='todo',
            name='position',
        ),
        migrations.DeleteModel(
            name='ToDoGroup',
        ),
    ]
