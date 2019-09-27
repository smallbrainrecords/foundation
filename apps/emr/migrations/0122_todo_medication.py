# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0121_taggedtodoorder_created_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='medication',
            field=models.ForeignKey(to='emr.Medication', null=True),
        ),
    ]
