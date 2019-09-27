# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0047_auto_20160420_2130'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationcomponent',
            name='created_on',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
