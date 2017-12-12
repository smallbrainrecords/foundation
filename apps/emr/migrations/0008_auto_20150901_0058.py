# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0007_auto_20150824_0111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(default=b'patient', max_length=10, choices=[(b'patient', b'Patient'), (b'physician', b'Physician'), (b'mid-level', b'Mid Level PA/NP'), (b'nurse', b'Nurse'), (b'secretary', b'Secretary'), (b'admin', b'Admin')]),
        ),
    ]
