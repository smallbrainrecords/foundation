# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0107_auto_20161118_1709'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField()),
                ('path', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(related_name='author_document', to='emr.UserProfile', on_delete=models.DO_NOTHING)),
                ('patient',
                 models.ForeignKey(related_name='patient_pinned', blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING)),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
    ]
