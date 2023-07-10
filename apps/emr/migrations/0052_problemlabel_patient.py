# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0051_auto_20160506_2007'),
    ]

    operations = [
        migrations.AddField(
            model_name='problemlabel',
            name='patient',
            field=models.ForeignKey(related_name='problem_label_patient', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True, on_delete=models.DO_NOTHING),
        ),
    ]
