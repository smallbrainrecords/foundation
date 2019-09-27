# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0073_auto_20160728_0958'),
    ]

    operations = [
        migrations.AddField(
            model_name='coloncancerscreening',
            name='todo_past_five_years',
            field=models.BooleanField(default=False),
        ),
    ]
