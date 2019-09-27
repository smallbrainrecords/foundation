# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0129_generalsetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='labeledtodolist',
            name='private',
            field=models.BooleanField(default=0),
        ),
    ]
