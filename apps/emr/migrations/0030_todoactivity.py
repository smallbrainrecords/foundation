# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0029_encountertodorecord'),
    ]

    operations = [
        migrations.CreateModel(
            name='TodoActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activity', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('attachment', models.ForeignKey(blank=True, to='emr.ToDoAttachment', null=True, on_delete=models.DO_NOTHING)),
                ('author', models.ForeignKey(blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING)),
                ('comment', models.ForeignKey(blank=True, to='emr.ToDoComment', null=True, on_delete=models.DO_NOTHING)),
                ('todo', models.ForeignKey(to='emr.ToDo', on_delete=models.DO_NOTHING)),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
    ]
