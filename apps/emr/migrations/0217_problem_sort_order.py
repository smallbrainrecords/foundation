"""The chart's problem order (2026-11-24; `Problem.sort_order`,
`mobile_problem_order`).

One operation, on purpose (MySQL DDL is not transactional). On production run
it by the migrate job BEFORE the revision that uses it serves: the chart pull
reads the column.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0216_missingstoredfile'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='sort_order',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
