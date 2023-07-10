# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
from emr.models import ColonCancerScreening, UserProfile


def changer_user_profile_id_to_user_id(apps, schema_editor):
    activities = ColonCancerScreening.objects.all()
    for act in activities:
        if UserProfile.objects.filter(id=act.patient_id).first() is not None:
            act.patient_id = UserProfile.objects.filter(id=act.patient_id).first().user_id

        if UserProfile.objects.filter(id=act.last_risk_updated_user_id).first() is not None:
            act.last_risk_updated_user_id = UserProfile.objects.filter(id=act.last_risk_updated_user_id).first().user_id
        act.save()


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0146_auto_20171116_0223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coloncancerscreening',
            name='last_risk_updated_user',
            field=models.ForeignKey(related_name='last_risk_updated_user_colons', blank=True,
                                    to=settings.AUTH_USER_MODEL, null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='coloncancerscreening',
            name='patient',
            field=models.ForeignKey(related_name='patient_colon_cancer', to=settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING),
        ),
        migrations.RunPython(changer_user_profile_id_to_user_id)
    ]
