# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0078_auto_20160822_0343'),
    ]

    operations = [
        migrations.AddField(
            model_name='mystorytextcomponent',
            name='private',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='mystorytextcomponententry',
            name='private',
            field=models.BooleanField(default=True),
        ),
    ]
