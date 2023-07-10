# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0011_auto_20150913_0210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemnote',
            name='author',
            field=models.ForeignKey(blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING),
        ),
    ]
