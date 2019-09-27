# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0091_auto_20160919_2117'),
    ]

    operations = [
        migrations.AlterField(
            model_name='todo',
            name='group',
            field=models.ForeignKey(related_name='items', blank=True, to='emr.ToDoGroup', null=True),
        ),
    ]
