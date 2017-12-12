# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0024_auto_20160115_0417'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='order',
            field=models.BigIntegerField(null=True, blank=True),
        ),
    ]
