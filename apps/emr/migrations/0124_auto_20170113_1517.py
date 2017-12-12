# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0123_problem_medications'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medication',
            name='name',
            field=models.TextField(),
        ),
    ]
