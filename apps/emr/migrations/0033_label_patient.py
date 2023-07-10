# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0032_auto_20160302_0121'),
    ]

    operations = [
        migrations.AddField(
            model_name='label',
            name='patient',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING),
        ),
    ]
