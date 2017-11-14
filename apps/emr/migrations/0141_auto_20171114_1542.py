# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

from emr.models import Observation, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = Observation.objects.all()
    for act in activities:
        if UserProfile.objects.filter(id=act.subject_id).first() is not None:
            act.subject_id = UserProfile.objects.filter(id=act.subject_id).first().user_id
        if UserProfile.objects.filter(id=act.encounter_id).first() is not None:
            act.encounter_id = UserProfile.objects.filter(id=act.encounter_id).first().user_id
        if UserProfile.objects.filter(id=act.performer_id).first() is not None:
            act.performer_id = UserProfile.objects.filter(id=act.performer_id).first().user_id
        if UserProfile.objects.filter(id=act.author_id).first() is not None:
            act.author_id = UserProfile.objects.filter(id=act.author_id).first().user_id
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
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
