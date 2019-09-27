# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0110_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentProblem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='DocumentTodo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AlterField(
            model_name='document',
            name='document',
            field=models.FileField(null=True, upload_to=b'documents/'),
        ),
        migrations.AddField(
            model_name='documenttodo',
            name='document',
            field=models.ForeignKey(to='emr.Document'),
        ),
        migrations.AddField(
            model_name='documenttodo',
            name='todo',
            field=models.ForeignKey(to='emr.ToDo'),
        ),
        migrations.AddField(
            model_name='documentproblem',
            name='document',
            field=models.ForeignKey(to='emr.Document'),
        ),
        migrations.AddField(
            model_name='documentproblem',
            name='problem',
            field=models.ForeignKey(to='emr.Problem'),
        ),
    ]
