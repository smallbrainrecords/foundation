# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0082_observationpintoproblem'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationUnit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_unit', models.CharField(max_length=45, null=True, blank=True)),
                ('is_used', models.BooleanField(default=False)),
                ('observation', models.ForeignKey(related_name='observation_units', to='emr.Observation', on_delete=models.DO_NOTHING)),
            ],
        ),
    ]
