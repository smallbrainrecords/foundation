# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0008_auto_20150901_0058'),
    ]

    operations = [
        migrations.CreateModel(
            name='PhysicianTeam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('member', models.ForeignKey(related_name='user_leaders', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
                ('physician', models.ForeignKey(related_name='physician_helpers', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
            ],
        ),
    ]
