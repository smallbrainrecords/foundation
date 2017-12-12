# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0068_auto_20160727_0144'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coloncancerstudy',
            name='finding',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='coloncancerstudy',
            name='last_updated_user',
            field=models.ForeignKey(related_name='last_updated_user_studies', blank=True, to='emr.UserProfile', null=True),
        ),
    ]
