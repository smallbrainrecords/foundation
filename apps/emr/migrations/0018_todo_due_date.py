# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0017_auto_20151215_2222'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='due_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
