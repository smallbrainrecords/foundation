# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.models import F

from emr.models import Document


def seed_default_document_name(apps, schema_editor):
    Document.objects.update(document_name=F('document'))


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0131_auto_20170216_2241'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='document_name',
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(seed_default_document_name)
    ]
