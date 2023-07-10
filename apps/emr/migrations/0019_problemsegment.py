# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0018_todo_due_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemSegment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_controlled', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('authenticated', models.BooleanField(default=False)),
                ('start_date', models.DateField(auto_now_add=True)),
                ('problem', models.ForeignKey(to='emr.Problem', on_delete=models.DO_NOTHING)),
            ],
        ),
    ]
