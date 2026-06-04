# Adds client_uuid (nullable, unique, indexed) to Encounter and EncounterEvent
# to support idempotent retries from the iOS mobile_api push paths. The iOS
# SwiftData syncID UUID is sent over the wire as client_uuid, and the Django
# create/update views use update_or_create(client_uuid=...) so a network blip
# can't produce duplicate rows on retry.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0171_encounter_transcript'),
    ]

    operations = [
        migrations.AddField(
            model_name='encounter',
            name='client_uuid',
            field=models.UUIDField(null=True, blank=True, unique=True, db_index=True),
        ),
        migrations.AddField(
            model_name='encounterevent',
            name='client_uuid',
            field=models.UUIDField(null=True, blank=True, unique=True, db_index=True),
        ),
    ]
