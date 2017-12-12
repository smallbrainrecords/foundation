# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0037_labeledtodolist_todo_list'),
    ]

    operations = [
        migrations.AddField(
            model_name='label',
            name='author',
            field=models.ForeignKey(related_name='label_author', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='label',
            name='is_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='label',
            name='user',
            field=models.ForeignKey(related_name='label_user', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
