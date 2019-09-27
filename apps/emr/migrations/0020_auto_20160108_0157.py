# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0019_problemsegment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemsegment',
            name='start_date',
            field=models.DateField(),
        ),
    ]
