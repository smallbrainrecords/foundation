# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0125_auto_20170123_0923'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taggedtodoorder',
            name='status',
            field=models.IntegerField(default=0, choices=[(0, b'New'), (1, b'Seen'), (2, b'Viewed')]),
        ),
    ]
