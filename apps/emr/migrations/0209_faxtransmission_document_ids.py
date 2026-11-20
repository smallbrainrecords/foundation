# Faxing chart documents (2026-11-18): the documents a chart fax carried.
# One operation.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0208_faxpatientmatch'),
    ]

    operations = [
        migrations.AddField(
            model_name='faxtransmission',
            name='document_ids',
            field=models.TextField(default='[]'),
        ),
    ]
