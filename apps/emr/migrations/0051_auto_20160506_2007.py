# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0050_observationcomponent_author'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProblemLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(null=True, blank=True)),
                ('css_class', models.TextField(null=True, blank=True)),
                ('author',
                 models.ForeignKey(related_name='problem_label_author', blank=True, to=settings.AUTH_USER_MODEL,
                                   null=True, on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.AddField(
            model_name='problem',
            name='labels',
            field=models.ManyToManyField(to='emr.ProblemLabel', blank=True),
        ),
    ]
