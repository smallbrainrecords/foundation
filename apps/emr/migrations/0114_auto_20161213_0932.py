# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0113_auto_20161212_2209'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='inrtextnote',
            name='inr',
        ),
        migrations.AddField(
            model_name='inrtextnote',
            name='patient',
            field=models.ForeignKey(related_name='patient_note', to='emr.UserProfile', on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='inrtextnote',
            name='author',
            field=models.ForeignKey(related_name='author_note', to='emr.UserProfile', on_delete=models.DO_NOTHING),
        ),
    ]
