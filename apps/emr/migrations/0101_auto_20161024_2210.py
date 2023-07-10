# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0100_auto_20161017_2239'),
    ]

    operations = [
        migrations.CreateModel(
            name='InrTextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(to='emr.UserProfile', on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.RemoveField(
            model_name='medication',
            name='inr',
        ),
        migrations.AddField(
            model_name='inr',
            name='author',
            field=models.ForeignKey(related_name='author_inrs', blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='inr',
            name='pin',
            field=models.ForeignKey(related_name='observation_inrs', blank=True, to='emr.ObservationPinToProblem',
                                    null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='inrvalue',
            name='current_dose',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inrvalue',
            name='new_dosage',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='inrvalue',
            name='next_inr',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='medication',
            name='patient',
            field=models.ForeignKey(related_name='patient_medications', blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='inr',
            name='patient',
            field=models.ForeignKey(related_name='patient_inrs', to='emr.UserProfile', on_delete=models.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='inrtextnote',
            name='inr',
            field=models.ForeignKey(related_name='inr_notes', to='emr.Inr', on_delete=models.DO_NOTHING),
        ),
    ]
