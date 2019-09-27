# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0023_auto_20160115_0416'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problemsegment',
            options={'ordering': ('start_date', 'start_time')},
        ),
    ]
