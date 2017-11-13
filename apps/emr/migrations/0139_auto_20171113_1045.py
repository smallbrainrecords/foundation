# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

from emr.models import ProblemNote, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = ProblemNote.objects.all()
    for act in activities:
        act.author_id = UserProfile.objects.filter(id=act.author_id).first().user_id
        act.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0138_auto_20171113_0942'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problemnote',
            name='author',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
