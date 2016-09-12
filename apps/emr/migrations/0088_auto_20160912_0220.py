# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0087_auto_20160909_1150'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationValueTextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, to='emr.UserProfile', null=True)),
                ('observation_value', models.ForeignKey(related_name='observation_value_notes', to='emr.ObservationValue')),
            ],
        ),
        migrations.RemoveField(
            model_name='observationcomponenttextnote',
            name='author',
        ),
        migrations.RemoveField(
            model_name='observationcomponenttextnote',
            name='observation_component',
        ),
        migrations.DeleteModel(
            name='ObservationComponentTextNote',
        ),
    ]
