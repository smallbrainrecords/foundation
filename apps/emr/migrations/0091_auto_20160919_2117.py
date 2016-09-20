# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0090_auto_20160919_2114'),
    ]

    operations = [
        migrations.RenameField(
            model_name='todo',
            old_name='group_id',
            new_name='group',
        ),
    ]
