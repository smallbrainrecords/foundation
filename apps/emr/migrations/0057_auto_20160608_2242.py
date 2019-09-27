# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0056_problem_old_problem_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='encounterevent',
            name='is_favorite',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='encounterevent',
            name='name_favorite',
            field=models.TextField(null=True, blank=True),
        ),
    ]
