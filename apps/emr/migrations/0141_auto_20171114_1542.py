# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

from emr.models import Observation, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = Observation.objects.all()
    for act in activities:
        act.subject = UserProfile.objects.filter(id=act.subject).first().user_id
        act.encounter = UserProfile.objects.filter(id=act.encounter).first().user_id
        act.performer = UserProfile.objects.filter(id=act.performer).first().user_id
        act.author = UserProfile.objects.filter(id=act.author).first().user_id
        act.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0140_auto_20171113_1132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observation',
            name='author',
            field=models.ForeignKey(related_name='observation_authors', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='encounter',
            field=models.ForeignKey(related_name='observation_encounters', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='performer',
            field=models.ForeignKey(related_name='observation_performers', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='subject',
            field=models.ForeignKey(related_name='observation_subjects', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True),
        ),
    ]
