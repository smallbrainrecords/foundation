# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0089_mystorytab_tab_all'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToDoGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(null=True, blank=True)),
                ('position', models.IntegerField(null=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='todo',
            name='position',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='todo',
            name='group_id',
            field=models.ForeignKey(blank=True, to='emr.ToDoGroup', null=True),
        ),
    ]
