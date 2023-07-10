# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0027_auto_20160203_0257'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToDoAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(upload_to=b'attachments/', blank=True)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('todo', models.ForeignKey(related_name='attachments', to='emr.ToDo', on_delete=models.DO_NOTHING)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.AlterField(
            model_name='todocomment',
            name='todo',
            field=models.ForeignKey(related_name='comments', to='emr.ToDo', on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='todolabel',
            name='todo',
            field=models.ForeignKey(related_name='labels', to='emr.ToDo', on_delete=models.DO_NOTHING),
        ),
    ]
