# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0161_narrative'),
    ]

    operations = [
        migrations.AlterField(
            model_name='narrative',
            name='parent',
            field=models.ForeignKey(related_name='child', to='emr.Narrative', null=True, on_delete=models.DO_NOTHING),
        ),
    ]
