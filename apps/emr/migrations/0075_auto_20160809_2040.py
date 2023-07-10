# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0074_coloncancerscreening_todo_past_five_years'),
    ]

    operations = [
        migrations.AddField(
            model_name='coloncancerscreening',
            name='not_appropriate',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='todo',
            name='colon_cancer',
            field=models.ForeignKey(related_name='colon_cancer_todos', blank=True, to='emr.ColonCancerScreening',
                                    null=True, on_delete=models.DO_NOTHING),
        ),
    ]
