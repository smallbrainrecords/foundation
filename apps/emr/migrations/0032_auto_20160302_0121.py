# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0031_todo_members'),
    ]

    operations = [
        migrations.CreateModel(
            name='Label',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(null=True, blank=True)),
                ('css_class', models.TextField(null=True, blank=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='todolabel',
            name='todo',
        ),
        migrations.DeleteModel(
            name='ToDoLabel',
        ),
        migrations.AddField(
            model_name='todo',
            name='labels',
            field=models.ManyToManyField(to='emr.Label', blank=True),
        ),
    ]
