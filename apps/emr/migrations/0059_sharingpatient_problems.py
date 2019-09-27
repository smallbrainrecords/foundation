# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0058_todo_created_on'),
    ]

    operations = [
        migrations.AddField(
            model_name='sharingpatient',
            name='problems',
            field=models.ManyToManyField(related_name='sharing_problems', to='emr.Problem', blank=True),
        ),
    ]
