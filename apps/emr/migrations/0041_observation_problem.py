# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0040_auto_20160406_2334'),
    ]

    operations = [
        migrations.AddField(
            model_name='observation',
            name='problem',
            field=models.ForeignKey(related_name='problem_observations', default=1, to='emr.Problem', on_delete=models.DO_NOTHING),
            preserve_default=False,
        ),
    ]
