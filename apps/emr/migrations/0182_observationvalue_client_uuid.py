from django.db import migrations, models


def add_client_uuid_if_missing(apps, schema_editor):
    # Prod drift, discovered when this migration first deployed (revision
    # 00085-xpd boot failure, 2026-07-17): emr_observationvalue ALREADY
    # carries a client_uuid char(32) UNIQUE NULL column of unknown vintage —
    # present in the 2026-07-06 prod snapshot with cardinality 0 (never
    # written) and no django_migrations record. Its shape is exactly what
    # Django's UUIDField(null=True, unique=True, db_index=True) produces, so
    # where it exists we record state and touch nothing; fresh schemas (test
    # databases, new environments) get the real DDL below. The test suite
    # exercises the DDL path on every run (fresh test database).
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        columns = [
            col.name
            for col in connection.introspection.get_table_description(
                cursor, 'emr_observationvalue')
        ]
    if 'client_uuid' in columns:
        return
    # RunPython receives the PRE-migration state (from_state.apps), so the
    # historical model doesn't carry the field yet — build it directly.
    ObservationValue = apps.get_model('emr', 'ObservationValue')
    field = models.UUIDField(blank=True, db_index=True, null=True, unique=True)
    field.set_attributes_from_name('client_uuid')
    schema_editor.add_field(ObservationValue, field)


class Migration(migrations.Migration):
    """Additive + nullable + drift-tolerant: safe under the boot-time
    auto-migrate deploy (init-cloudrun.sh). The unique index is the
    idempotency guarantee for retried value creates."""

    dependencies = [
        ('emr', '0181_observation_client_uuid'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='observationvalue',
                    name='client_uuid',
                    field=models.UUIDField(
                        blank=True, db_index=True, null=True, unique=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(
                    add_client_uuid_if_missing, migrations.RunPython.noop),
            ],
        ),
    ]
