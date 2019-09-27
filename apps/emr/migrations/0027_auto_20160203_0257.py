# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0026_todocomment'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToDoLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(null=True, blank=True)),
                ('css_class', models.TextField(null=True, blank=True)),
                ('todo', models.ForeignKey(related_name='todo_label', to='emr.ToDo')),
            ],
        ),
        migrations.AlterField(
            model_name='todocomment',
            name='comment',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='todocomment',
            name='datetime',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
