# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0021_auto_20160111_2140'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problemsegment',
            options={'ordering': ('start_date',)},
        ),
    ]
