# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0160_add_phq_2_for_all_users_20180318_1124'),
    ]

    operations = [
        migrations.CreateModel(
            name='Narrative',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(related_name='owned_narratives', to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(related_name='child', to='emr.Narrative')),
                ('patient', models.ForeignKey(related_name='patient_narratives', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
