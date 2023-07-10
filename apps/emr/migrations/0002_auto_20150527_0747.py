# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='encounter',
            name='events',
        ),
        migrations.RemoveField(
            model_name='encounterevent',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='encounterevent',
            name='object_id',
        ),
        migrations.AddField(
            model_name='encounterevent',
            name='encounter',
            field=models.ForeignKey(related_name='encounter_events', blank=True, to='emr.Encounter', null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='encounterevent',
            name='summary',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='encounter',
            name='patient',
            field=models.ForeignKey(related_name='patient_encounters', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='encounter',
            name='physician',
            field=models.ForeignKey(related_name='physician_encounters', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING),
        ),
    ]
