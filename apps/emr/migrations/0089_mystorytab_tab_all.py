# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0088_auto_20160912_0220'),
    ]

    operations = [
        migrations.AddField(
            model_name='mystorytab',
            name='tab_all',
            field=models.BigIntegerField(null=True, blank=True),
        ),
    ]
