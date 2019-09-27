# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0069_auto_20160727_0351'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coloncancerstudy',
            options={'ordering': ['-study_date']},
        ),
        migrations.RemoveField(
            model_name='coloncancerstudy',
            name='report_images',
        ),
        migrations.AddField(
            model_name='coloncancerstudyimage',
            name='author',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='coloncancerstudyimage',
            name='colon',
            field=models.ForeignKey(blank=True, to='emr.ColonCancerScreening', null=True),
        ),
        migrations.AddField(
            model_name='coloncancerstudyimage',
            name='datetime',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
