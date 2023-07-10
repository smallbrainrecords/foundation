# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0117_inr_patient'),
    ]

    operations = [
        migrations.AddField(
            model_name='medication',
            name='search_str',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='inr',
            name='observation_value',
            field=models.OneToOneField(related_name='inr', null=True, to='emr.ObservationValue', on_delete=models.DO_NOTHING),
        ),
    ]
