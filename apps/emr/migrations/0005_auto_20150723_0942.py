# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0004_auto_20150607_1018'),
    ]

    operations = [
        migrations.AddField(
            model_name='textnote',
            name='author',
            field=models.ForeignKey(blank=True, to='emr.UserProfile', null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='sex',
            field=models.CharField(blank=True, max_length=6, choices=[(b'male', b'Male'), (b'female', b'Female')]),
        ),
    ]
