# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0108_document'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='name',
        ),
        migrations.RemoveField(
            model_name='document',
            name='path',
        ),
        migrations.AddField(
            model_name='document',
            name='document',
            field=models.FileField(null=True, upload_to=b'/documents'),
        ),
    ]
