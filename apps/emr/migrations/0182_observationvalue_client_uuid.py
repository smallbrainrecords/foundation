from django.db import migrations, models


class Migration(migrations.Migration):
    """Additive + nullable: safe under the boot-time auto-migrate deploy
    (init-cloudrun.sh) and imposes nothing on existing rows. Unique index
    is the idempotency guarantee for retried value creates."""

    dependencies = [
        ('emr', '0181_observation_client_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationvalue',
            name='client_uuid',
            field=models.UUIDField(blank=True, db_index=True, null=True, unique=True),
        ),
    ]
