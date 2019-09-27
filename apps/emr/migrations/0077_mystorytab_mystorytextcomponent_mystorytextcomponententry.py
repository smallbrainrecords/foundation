# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0076_auto_20160809_2238'),
    ]

    operations = [
        migrations.CreateModel(
            name='MyStoryTab',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('private', models.BooleanField(default=True)),
                ('shared', models.BooleanField(default=True)),
                ('patient', models.ForeignKey(related_name='patient_story_tabs', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MyStoryTextComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(null=True, blank=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('last_updated_date', models.DateField(auto_now=True)),
                ('concept_id', models.CharField(max_length=20, null=True, blank=True)),
                ('last_updated_user', models.ForeignKey(blank=True, to='emr.UserProfile', null=True)),
                ('patient', models.ForeignKey(related_name='patient_story_texts', to=settings.AUTH_USER_MODEL)),
                ('tab', models.ForeignKey(blank=True, to='emr.MyStoryTab', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MyStoryTextComponentEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('text', models.TextField(null=True, blank=True)),
                ('datetime', models.DateTimeField(null=True, blank=True)),
                ('author', models.ForeignKey(related_name='author_story_text_entries', to=settings.AUTH_USER_MODEL)),
                ('component', models.ForeignKey(blank=True, to='emr.MyStoryTextComponent', null=True)),
            ],
        ),
    ]
