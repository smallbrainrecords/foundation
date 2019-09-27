# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0092_auto_20160920_1115'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='todogroup',
            name='position',
        ),
        migrations.AddField(
            model_name='todogroup',
            name='order',
            field=models.BigIntegerField(null=True, blank=True),
        ),
    ]
