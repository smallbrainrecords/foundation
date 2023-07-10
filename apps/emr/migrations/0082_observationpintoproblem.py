# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0081_auto_20160824_2229'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationPinToProblem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.ForeignKey(related_name='pin_authors', blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING)),
                ('observation',
                 models.ForeignKey(related_name='pin_observations', blank=True, to='emr.Observation', null=True, on_delete=models.DO_NOTHING)),
                ('problem', models.ForeignKey(related_name='pin_problems', blank=True, to='emr.Problem', null=True, on_delete=models.DO_NOTHING)),
            ],
        ),
    ]
