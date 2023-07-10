# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from emr.models import Inr, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = Inr.objects.all()
    for act in activities:
        if UserProfile.objects.filter(id=act.author_id).first() is not None:
            act.author_id = UserProfile.objects.filter(id=act.author_id).first().user_id
        if UserProfile.objects.filter(id=act.patient_id).first() is not None:
            act.patient_id = UserProfile.objects.filter(id=act.patient_id).first().user_id
        act.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0150_auto_20171116_1439'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inr',
            name='author',
            field=models.ForeignKey(related_name='author_inr', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='inr',
            name='patient',
            field=models.ForeignKey(related_name='patient_inr', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
