# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0003_auto_20150527_0748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goal',
            name='start_date',
            field=models.DateField(auto_now_add=True),
        ),
    ]
