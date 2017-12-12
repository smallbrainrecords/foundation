# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0002_auto_20150527_0747'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventsummary',
            name='patient',
        ),
        migrations.AlterField(
            model_name='encounterevent',
            name='summary',
            field=models.TextField(default=b''),
        ),
        migrations.DeleteModel(
            name='EventSummary',
        ),
    ]
