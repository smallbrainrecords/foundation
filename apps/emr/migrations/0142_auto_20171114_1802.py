# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

from emr.models import ObservationComponent, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = ObservationComponent.objects.all()
    for act in activities:
        if UserProfile.objects.filter(id=act.author_id).first() is not None:
            act.author_id = UserProfile.objects.filter(id=act.author_id).first().user_id
        act.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0141_auto_20171114_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='observationcomponent',
            name='author',
            field=models.ForeignKey(related_name='observation_component_authors', blank=True,
                                    to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
