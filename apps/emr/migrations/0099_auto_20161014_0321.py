# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0098_auto_20161004_1120'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mystorytab',
            name='tab_all',
        ),
        migrations.RemoveField(
            model_name='mystorytextcomponent',
            name='text',
        ),
        migrations.RemoveField(
            model_name='mystorytextcomponententry',
            name='private',
        ),
        migrations.AddField(
            model_name='mystorytextcomponententry',
            name='patient',
            field=models.ForeignKey(related_name='patient_story_text_entries', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True),
        ),
        migrations.AlterField(
            model_name='mystorytextcomponententry',
            name='datetime',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
