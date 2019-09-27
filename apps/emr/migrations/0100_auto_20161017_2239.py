# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0099_auto_20161014_0321'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mystorytextcomponent',
            name='last_updated_date',
        ),
        migrations.RemoveField(
            model_name='mystorytextcomponent',
            name='last_updated_user',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='active_reason',
            field=models.TextField(null=True, blank=True),
        ),
    ]
