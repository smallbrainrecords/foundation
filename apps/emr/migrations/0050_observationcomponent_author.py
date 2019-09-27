# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0049_auto_20160428_2117'),
    ]

    operations = [
        migrations.AddField(
            model_name='observationcomponent',
            name='author',
            field=models.ForeignKey(related_name='observation_component_authors', blank=True, to='emr.UserProfile',
                                    null=True),
        ),
    ]
