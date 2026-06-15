# Generated 2026-06-14 — adds Todo.accomplished_at + backfills historical rows.

from django.db import migrations, models


def backfill_accomplished_at(apps, schema_editor):
    """Populate accomplished_at for existing accomplished todos using
    created_on as the best-available approximation. Django ToDo has no
    updated_at column, so historical timestamps are inherently imprecise.
    New accomplishments going forward are stamped accurately by
    ToDo.save()."""
    ToDo = apps.get_model('emr', 'ToDo')
    ToDo.objects.filter(
        accomplished=True,
        accomplished_at__isnull=True,
    ).update(accomplished_at=models.F('created_on'))


def clear_accomplished_at(apps, schema_editor):
    """Reverse migration — clear the field so the schema add can be rolled
    back cleanly."""
    ToDo = apps.get_model('emr', 'ToDo')
    ToDo.objects.update(accomplished_at=None)


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0176_document_unassigned_pool_columns'),
    ]

    operations = [
        migrations.AddField(
            model_name='todo',
            name='accomplished_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
        migrations.RunPython(backfill_accomplished_at, clear_accomplished_at),
    ]
