# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0136_update_diabetes_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='textnote',
            name='author',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING),
        ),
    ]
