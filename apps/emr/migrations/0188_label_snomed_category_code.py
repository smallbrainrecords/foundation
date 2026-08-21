"""Add Label.snomed_category_code.

Deliberately a SINGLE AddField: concurrent Cloud Run boots race `migrate` with
no lock on MySQL, and a multi-operation migration that dies between operations
is never recorded, so every subsequent boot re-attempts it and fails on the
already-applied first step. One operation cannot strand.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0187_document_extracted_text'),
    ]

    operations = [
        migrations.AddField(
            model_name='label',
            name='snomed_category_code',
            field=models.CharField(blank=True, max_length=18, null=True),
        ),
    ]
