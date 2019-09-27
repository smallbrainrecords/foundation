# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0104_auto_20161104_1046'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inr',
            name='problem',
        ),
        migrations.AddField(
            model_name='problem',
            name='inr',
            field=models.ForeignKey(related_name='inr_problem', blank=True, to='emr.Inr', null=True),
        ),
        migrations.AlterField(
            model_name='inr',
            name='target',
            field=models.PositiveIntegerField(choices=[(1, b'2-3'), (0, b'2.5-3.5')]),
        ),
    ]
