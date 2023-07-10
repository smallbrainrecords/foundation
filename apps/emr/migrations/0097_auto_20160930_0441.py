# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0096_auto_20160929_2155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inr',
            name='patient',
            field=models.OneToOneField(related_name='patient_inr', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING),
        ),
    ]
