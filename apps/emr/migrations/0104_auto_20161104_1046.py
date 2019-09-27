# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0103_inr_target'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inr',
            name='target',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
