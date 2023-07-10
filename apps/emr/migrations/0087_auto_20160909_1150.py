# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0086_auto_20160906_0142'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mystorytextcomponententry',
            options={'ordering': ['-datetime']},
        ),
        migrations.AddField(
            model_name='observation',
            name='graph',
            field=models.TextField(default=b'Line'),
        ),
        migrations.AlterField(
            model_name='mystorytextcomponententry',
            name='author',
            field=models.ForeignKey(related_name='author_story_text_entries', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True, on_delete=models.DO_NOTHING),
        ),
    ]
