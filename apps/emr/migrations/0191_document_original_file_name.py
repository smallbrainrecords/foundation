# One operation on purpose: migrations run on container boot with no lock on
# MySQL, and a single AddField leaves no partial state for a racing boot to
# strand (see CLAUDE.md, "Concurrent boots race the migration").

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0190_observationvalueaudit'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='original_file_name',
            field=models.TextField(blank=True, null=True),
        ),
    ]
