# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from emr.models import ColonCancerStudy, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = ColonCancerStudy.objects.all()
    for act in activities:
        if UserProfile.objects.filter(id=act.author_id).first() is not None:
            act.author_id = UserProfile.objects.filter(id=act.author_id).first().user_id

        if UserProfile.objects.filter(id=act.last_updated_user_id).first() is not None:
            act.last_updated_user_id = UserProfile.objects.filter(id=act.last_updated_user_id).first().user_id
        act.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0147_auto_20171116_0232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coloncancerstudy',
            name='author',
            field=models.ForeignKey(related_name='author_studies', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='coloncancerstudy',
            name='last_updated_user',
            field=models.ForeignKey(related_name='last_updated_user_studies', blank=True, to=settings.AUTH_USER_MODEL,
                                    null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
