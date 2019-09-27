# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0013_problemactivity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemactivity',
            name='author',
            field=models.ForeignKey(blank=True, to='emr.UserProfile', null=True),
        ),
    ]
