"""The offline copy's file list reads this index alone (2026-11-22).

One operation, on purpose (MySQL DDL is not transactional). On production run
it by the migrate job BEFORE the revision that uses it serves.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0214_portraithistory'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='document',
            index=models.Index(
                fields=['created_on', 'patient', 'document', 'file_size'],
                name='emr_doc_created_file_idx',
            ),
        ),
    ]
