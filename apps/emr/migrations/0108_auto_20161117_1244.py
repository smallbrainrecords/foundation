# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0107_auto_20161115_2056'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='problem',
            name='inr',
        ),
        migrations.AddField(
            model_name='inr',
            name='problem',
            field=models.ForeignKey(related_name='problem_pin_inrs', blank=True, to='emr.Problem', null=True),
        ),
    ]
