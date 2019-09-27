# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0034_auto_20160311_2028'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaggedToDoOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('order', models.BigIntegerField(null=True, blank=True)),
                ('todo', models.ForeignKey(blank=True, to='emr.ToDo', null=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
