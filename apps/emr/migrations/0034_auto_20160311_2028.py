# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0033_label_patient'),
    ]

    operations = [
        migrations.RenameField(
            model_name='label',
            old_name='patient',
            new_name='user',
        ),
        migrations.AddField(
            model_name='todo',
            name='user',
            field=models.ForeignKey(related_name='todo_owner', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='todo',
            name='patient',
            field=models.ForeignKey(related_name='todo_patient', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
