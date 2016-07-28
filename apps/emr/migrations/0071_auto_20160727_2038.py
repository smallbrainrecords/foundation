# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0070_auto_20160727_1134'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coloncancerstudyimage',
            name='colon',
        ),
        migrations.AddField(
            model_name='coloncancerstudyimage',
            name='study',
            field=models.ForeignKey(blank=True, to='emr.ColonCancerStudy', null=True),
        ),
        migrations.AlterField(
            model_name='coloncancerstudyimage',
            name='author',
            field=models.ForeignKey(blank=True, to='emr.UserProfile', null=True),
        ),
    ]
