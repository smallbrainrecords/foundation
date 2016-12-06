# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0110_auto_20161127_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='labels',
            field=models.ManyToManyField(to='emr.Label'),
        ),
    ]
