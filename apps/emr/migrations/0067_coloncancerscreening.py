# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0066_auto_20160713_2129'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColonCancerScreening',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('patient_refused', models.BooleanField(default=False)),
                ('patient', models.ForeignKey(related_name='patient_colon_cancer', to='emr.UserProfile')),
                ('problem', models.ForeignKey(related_name='problem_colon_cancer', to='emr.Problem')),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
    ]
