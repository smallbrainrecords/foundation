# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0060_labeledproblemlist_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='encounterevent',
            name='timestamp',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
