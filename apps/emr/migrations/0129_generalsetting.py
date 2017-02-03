# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from emr.models import GeneralSetting


def init_general_settings(apps, schema_editor):
    browserAudioRecording = GeneralSetting(setting_key='browser_audio_recording', setting_value='true')
    browserAudioRecording.save()
    todoPopupConfirm = GeneralSetting(setting_key='todo_popup_confirm', setting_value='[]')
    todoPopupConfirm.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0128_auto_20170203_1508'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneralSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('setting_key', models.TextField()),
                ('setting_value', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RunPython(init_general_settings)
    ]
