# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0084_auto_20160905_2151'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationfield',
            name='code',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
    ]
