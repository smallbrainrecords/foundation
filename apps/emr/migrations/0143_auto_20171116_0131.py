# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


def changer_user_profile_id_to_user_id(apps, schema_editor):
    # Historical models (repaired 2026-07-17): this originally imported the
    # LIVE ObservationValue/UserProfile from emr.models, so its SELECT
    # included every column added in later migrations — fresh-schema builds
    # (test databases, new environments) crashed here the first time
    # ObservationValue gained a new field (0182's client_uuid). Prod
    # recorded this migration as applied in 2017, so only from-scratch
    # builds ever execute this function. Semantics unchanged.
    ObservationValue = apps.get_model('emr', 'ObservationValue')
    UserProfile = apps.get_model('emr', 'UserProfile')
    for act in ObservationValue.objects.all():
        profile = UserProfile.objects.filter(id=act.author_id).first()
        if profile is not None:
            act.author_id = profile.user_id
        act.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0142_auto_20171114_1802'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observationvalue',
            name='author',
            field=models.ForeignKey(related_name='observation_value_authors', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True, on_delete=models.SET_NULL),
        ),
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
