# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0116_auto_20161214_1140'),
    ]

    operations = [
        migrations.AddField(
            model_name='inr',
            name='patient',
            field=models.ForeignKey(related_name='patient_inr', to='emr.UserProfile', null=True),
        ),
    ]
