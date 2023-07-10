# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0111_document_labels'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='problems',
            field=models.ManyToManyField(to='emr.Problem', through='emr.DocumentProblem', blank=True),
        ),
        migrations.AddField(
            model_name='document',
            name='todos',
            field=models.ManyToManyField(to='emr.ToDo', through='emr.DocumentTodo', blank=True),
        ),
        migrations.AddField(
            model_name='documentproblem',
            name='author',
            field=models.ForeignKey(default=None, to='emr.UserProfile', on_delete=models.DO_NOTHING),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='documenttodo',
            name='author',
            field=models.ForeignKey(default=None, to='emr.UserProfile', on_delete=models.DO_NOTHING),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='document',
            name='labels',
            field=models.ManyToManyField(to='emr.Label', blank=True),
        ),
    ]
