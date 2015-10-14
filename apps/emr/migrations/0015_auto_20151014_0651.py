# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0014_auto_20151014_0629'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problemactivity',
            options={'ordering': ['-created_on']},
        ),
        migrations.AddField(
            model_name='problemactivity',
            name='created_on',
            field=models.DateTimeField(default=datetime.datetime(2015, 10, 14, 11, 51, 35, 83848, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
    ]
