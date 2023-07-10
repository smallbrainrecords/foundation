# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from emr.models import InrTextNote, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = InrTextNote.objects.all()
    for act in activities:
        if UserProfile.objects.filter(id=act.author_id).first() is not None:
            act.author_id = UserProfile.objects.filter(id=act.author_id).first().user_id
        if UserProfile.objects.filter(id=act.patient_id).first() is not None:
            act.patient_id = UserProfile.objects.filter(id=act.patient_id).first().user_id

        act.save()


migrations.RunPython(changer_user_profile_id_to_user_id)


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0151_auto_20171116_1455'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inrtextnote',
            name='author',
            field=models.ForeignKey(related_name='author_note', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='inrtextnote',
            name='patient',
            field=models.ForeignKey(related_name='patient_note', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING),
        ),
    ]
