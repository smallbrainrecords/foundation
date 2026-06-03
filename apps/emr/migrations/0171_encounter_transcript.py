# Adds Encounter.transcript so iOS clients can push Speech-framework transcripts
# back to the server and other devices see them under the bidirectional sync
# pipeline. Blank-allowed text field — historical rows pre-populate to ''.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0170_add_icd10_to_problem'),
    ]

    operations = [
        migrations.AddField(
            model_name='encounter',
            name='transcript',
            field=models.TextField(blank=True, default=''),
        ),
    ]
