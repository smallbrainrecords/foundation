# Faxing chart documents (2026-11-18): the PDF as sent, kept. One operation.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0209_faxtransmission_document_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='faxtransmission',
            name='file_path',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]
