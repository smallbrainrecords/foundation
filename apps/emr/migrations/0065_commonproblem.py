# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0064_auto_20160711_0907'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommonProblem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('problem_name', models.CharField(max_length=200)),
                ('concept_id', models.CharField(max_length=20, null=True, blank=True)),
                ('problem_type', models.CharField(default=b'acute', max_length=10,
                                                  choices=[(b'acute', b'Acute'), (b'chronic', b'Chronic')])),
                ('author',
                 models.ForeignKey(related_name='common_problem_author', blank=True, to=settings.AUTH_USER_MODEL,
                                   null=True, on_delete=models.DO_NOTHING)),
                ('patient', models.ForeignKey(related_name='common_problem_patient', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)),
            ],
        ),
    ]
