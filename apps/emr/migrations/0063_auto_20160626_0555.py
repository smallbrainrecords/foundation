# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0062_labeledtodolist_expanded'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='observationcomponent',
            options={'ordering': ['effective_datetime', 'created_on']},
        ),
    ]
