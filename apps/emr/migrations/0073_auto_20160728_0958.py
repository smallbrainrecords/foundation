# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0072_auto_20160728_0421'),
    ]

    operations = [
        migrations.AddField(
            model_name='coloncancerscreening',
            name='last_risk_updated_date',
            field=models.DateField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='coloncancerscreening',
            name='last_risk_updated_user',
            field=models.ForeignKey(related_name='last_risk_updated_user_colons', blank=True, to='emr.UserProfile',
                                    null=True, on_delete=models.DO_NOTHING),
        ),
    ]
