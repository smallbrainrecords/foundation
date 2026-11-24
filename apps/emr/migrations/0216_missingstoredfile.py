"""The files storage does not have, which the offline copy's list leaves
out (2026-11-24; `MissingStoredFile`, `check_offline_files`).

One operation, on purpose (MySQL DDL is not transactional). On production run
it by the migrate job BEFORE the revision that uses it serves.
"""
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0215_document_offline_copy_index'),
    ]

    operations = [
        migrations.CreateModel(
            name='MissingStoredFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=40, unique=True)),
                ('file_path', models.TextField()),
                ('checked_on', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
