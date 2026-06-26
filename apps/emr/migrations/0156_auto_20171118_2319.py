# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations




def changer_user_profile_id_to_user_id(apps, schema_editor):
    Document = apps.get_model('emr', 'Document')
    UserProfile = apps.get_model('emr', 'UserProfile')
    activities = Document.objects.all()
    for act in activities:
        try:
            author_profile = UserProfile.objects.filter(id=act.author_id).first()
            if author_profile is not None:
                act.author_id = author_profile.user_id
            
            patient_profile = UserProfile.objects.filter(id=act.patient_id).first()
            if patient_profile is not None:
                act.patient_id = patient_profile.user_id
            
            act.save()
        except Exception:
            continue


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0155_auto_20171118_2313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='author',
            field=models.ForeignKey(related_name='author_document', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='document',
            name='patient',
            field=models.ForeignKey(related_name='patient_pinned', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL),
        ),
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
