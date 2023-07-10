# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0010_auto_20150903_0947'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('note_type', models.CharField(max_length=50, choices=[(b'wiki', b'Wiki'), (b'history', b'History')])),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.RemoveField(
            model_name='problem',
            name='notes',
        ),
        migrations.AddField(
            model_name='problemnote',
            name='problem',
            field=models.ForeignKey(blank=True, to='emr.Problem', null=True, on_delete=models.DO_NOTHING),
        ),
    ]
