# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0077_mystorytab_mystorytextcomponent_mystorytextcomponententry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='mystorytab',
            name='shared',
        ),
        migrations.AddField(
            model_name='mystorytab',
            name='author',
            field=models.ForeignKey(related_name='author_story_tabs', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True),
        ),
        migrations.AddField(
            model_name='mystorytab',
            name='is_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='mystorytextcomponent',
            name='author',
            field=models.ForeignKey(related_name='author_story_texts', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True),
        ),
        migrations.AddField(
            model_name='mystorytextcomponent',
            name='is_all',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='sharingpatient',
            name='is_my_story_shared',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='mystorytextcomponent',
            name='last_updated_user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AlterField(
            model_name='mystorytextcomponent',
            name='tab',
            field=models.ForeignKey(related_name='my_story_tab_components', blank=True, to='emr.MyStoryTab', null=True),
        ),
        migrations.AlterField(
            model_name='mystorytextcomponententry',
            name='component',
            field=models.ForeignKey(related_name='text_component_entries', blank=True, to='emr.MyStoryTextComponent',
                                    null=True),
        ),
    ]
