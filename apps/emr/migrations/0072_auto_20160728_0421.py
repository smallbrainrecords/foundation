# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0071_auto_20160727_2038'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColonCancerTextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(blank=True, to='emr.UserProfile', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RiskFactor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('factor', models.CharField(max_length=100, null=True, blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='coloncancerscreening',
            name='risk',
            field=models.CharField(default=b'normal', max_length=10,
                                   choices=[(b'normal', b'Normal'), (b'high', b'High')]),
        ),
        migrations.AlterField(
            model_name='coloncancerstudyimage',
            name='study',
            field=models.ForeignKey(related_name='study_images', blank=True, to='emr.ColonCancerStudy', null=True),
        ),
        migrations.AddField(
            model_name='riskfactor',
            name='colon',
            field=models.ForeignKey(related_name='colon_risk_factors', to='emr.ColonCancerScreening'),
        ),
        migrations.AddField(
            model_name='coloncancertextnote',
            name='colon',
            field=models.ForeignKey(related_name='colon_notes', to='emr.ColonCancerScreening'),
        ),
    ]
