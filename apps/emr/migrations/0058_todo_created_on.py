# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0057_auto_20160608_2242'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
