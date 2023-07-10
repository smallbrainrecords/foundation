# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0012_auto_20150915_1120'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activity', models.TextField()),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
                ('problem', models.ForeignKey(to='emr.Problem', on_delete=models.DO_NOTHING)),
            ],
        ),
    ]
