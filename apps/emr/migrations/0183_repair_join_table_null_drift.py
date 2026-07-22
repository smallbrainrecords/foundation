from django.db import migrations


# Join-table columns whose models declare null=False but whose prod MySQL
# columns drifted to DEFAULT NULL (verified against the 2026-07-22 prod
# clone). Observed damage: 17 NULL observation_value_id rows (created_on
# spread 2022→2026 — an era of historical writes, not a single bad import;
# the live writers all pass ints) plus 126 NULL encounter_id rows across the
# three encounter join tables. A NULL id element made the entire patient_full
# payload undecodable on iOS (non-optional [Int]), taking whole charts down —
# 11 patients affected at time of repair (2026-07-22 incident). NULL
# encounter_id rows are unreachable garbage (every consumer iterates a
# per-encounter related set). The document link tables were verified
# non-drifted; they are listed anyway — the introspection guard makes extra
# entries free, and they are the same payload class on iOS.
JOIN_COLUMNS = [
    ('emr_encounterproblemrecord', 'encounter_id'),
    ('emr_encounterproblemrecord', 'problem_id'),
    ('emr_encountertodorecord', 'encounter_id'),
    ('emr_encountertodorecord', 'todo_id'),
    ('emr_encounterobservationvalue', 'encounter_id'),
    ('emr_encounterobservationvalue', 'observation_value_id'),
    ('emr_documentproblem', 'problem_id'),
    ('emr_documenttodo', 'document_id'),
    ('emr_documenttodo', 'todo_id'),
]


def clean_and_enforce_not_null(apps, schema_editor):
    """Delete orphaned NULL join rows, then re-assert the DB-level NOT NULL
    the models have always declared.

    Drift-tolerant both ways (same posture as 0182): a column that is already
    NOT NULL (fresh schemas, test databases, already-repaired prod) is left
    untouched, so the migration is idempotent and safe under the boot-time
    auto-migrate deploy (init-cloudrun.sh). The ALTER preserves the column's
    introspected type so nothing but nullability changes; the FK constraint
    survives a same-type MODIFY.
    """
    connection = schema_editor.connection
    if connection.vendor != 'mysql':
        # Non-MySQL engines only exist here as Django-created schemas, which
        # are born with the correct NOT NULL — nothing to repair.
        return
    with connection.cursor() as cursor:
        for table, column in JOIN_COLUMNS:
            cursor.execute(
                """
                SELECT COLUMN_TYPE, IS_NULLABLE
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s AND COLUMN_NAME = %s
                """,
                [table, column],
            )
            row = cursor.fetchone()
            if row is None:
                continue  # table absent in this environment
            column_type, is_nullable = row
            if is_nullable != 'YES':
                continue  # already correct
            cursor.execute(
                'DELETE FROM `%s` WHERE `%s` IS NULL' % (table, column)
            )
            cursor.execute(
                'ALTER TABLE `%s` MODIFY `%s` %s NOT NULL'
                % (table, column, column_type)
            )


class Migration(migrations.Migration):
    """Database-only repair — no state operations. Django's model state has
    always claimed null=False on these FKs; this brings the drifted MySQL
    columns back in line and removes the orphaned rows that violated it."""

    dependencies = [
        ('emr', '0182_observationvalue_client_uuid'),
    ]

    operations = [
        migrations.RunPython(
            clean_and_enforce_not_null, migrations.RunPython.noop),
    ]
