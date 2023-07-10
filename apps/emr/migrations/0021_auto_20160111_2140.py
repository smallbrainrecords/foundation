# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0020_auto_20160108_0157'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemsegment',
            name='event_id',
            field=models.BigIntegerField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='problemsegment',
            name='problem',
            field=models.ForeignKey(related_name='problem_segment', to='emr.Problem', on_delete=models.DO_NOTHING),
        ),
    ]
