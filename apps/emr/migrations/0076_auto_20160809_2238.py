# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0075_auto_20160809_2040'),
    ]

    operations = [
        migrations.AddField(
            model_name='coloncancerscreening',
            name='not_appropriate_on',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='coloncancerscreening',
            name='patient_refused_on',
            field=models.DateTimeField(null=True, blank=True),
        ),
    ]
