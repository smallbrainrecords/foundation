# Office documents (2026-11-18): a fax out of Office names the document it
# sent. One operation.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0205_officehandoff'),
    ]

    operations = [
        migrations.AddField(
            model_name='faxtransmission',
            name='document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='emr.document'),
        ),
    ]
