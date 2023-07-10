# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0079_auto_20160822_0455'),
    ]

    operations = [
        migrations.CreateModel(
            name='AOneC',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('todo_past_six_months', models.BooleanField(default=False)),
                ('patient_refused_A1C', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='AOneCTextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('a1c', models.ForeignKey(related_name='a1c_notes', to='emr.AOneC', on_delete=models.DO_NOTHING)),
                ('author', models.ForeignKey(blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.RemoveField(
            model_name='observationtextnote',
            name='author',
        ),
        migrations.RemoveField(
            model_name='observationtextnote',
            name='observation',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='patient_refused_A1C',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='problem',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='todo_past_six_months',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='value_codeableconcept',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='value_quantity',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='value_string',
        ),
        migrations.RemoveField(
            model_name='observation',
            name='value_unit',
        ),
        migrations.RemoveField(
            model_name='todo',
            name='observation',
        ),
        migrations.AddField(
            model_name='observation',
            name='name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='code',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='status',
            field=models.CharField(max_length=16, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='observation',
            name='subject',
            field=models.ForeignKey(related_name='observation_subjects', blank=True, to='emr.UserProfile', null=True, on_delete=models.DO_NOTHING),
        ),
        migrations.AlterField(
            model_name='observationcomponent',
            name='component_code',
            field=models.CharField(max_length=10, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='observationcomponent',
            name='status',
            field=models.CharField(max_length=16, null=True, blank=True),
        ),
        migrations.DeleteModel(
            name='ObservationTextNote',
        ),
        migrations.AddField(
            model_name='aonec',
            name='observation',
            field=models.OneToOneField(related_name='observation_aonecs', to='emr.Observation', on_delete=models.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='aonec',
            name='problem',
            field=models.OneToOneField(related_name='problem_aonecs', to='emr.Problem', on_delete=models.DO_NOTHING),
        ),
        migrations.AddField(
            model_name='todo',
            name='a1c',
            field=models.ForeignKey(related_name='a1c_todos', blank=True, to='emr.AOneC', null=True, on_delete=models.DO_NOTHING),
        ),
    ]
