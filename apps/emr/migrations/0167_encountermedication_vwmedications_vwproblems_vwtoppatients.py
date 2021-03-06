# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2020-04-26 04:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0166_add_top_patient_views'),
    ]

    operations = [
        migrations.CreateModel(
            name='VWMedications',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effectivetime', models.TextField()),
                ('active', models.TextField()),
                ('moduleid', models.TextField()),
                ('conceptid', models.TextField()),
                ('languagecode', models.TextField()),
                ('typeid', models.TextField()),
                ('term', models.TextField()),
                ('casesignificanceid', models.TextField()),
            ],
            options={
                'db_table': 'vw_medications',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VWProblems',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effectivetime', models.TextField()),
                ('active', models.TextField()),
                ('moduleid', models.TextField()),
                ('conceptid', models.TextField()),
                ('languagecode', models.TextField()),
                ('typeid', models.TextField()),
                ('term', models.TextField()),
                ('casesignificanceid', models.TextField()),
            ],
            options={
                'db_table': 'vw_problems',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='VWTopPatients',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('username', models.TextField()),
                ('name', models.TextField()),
                ('user_profile_id', models.IntegerField()),
                ('todo_count', models.IntegerField()),
                ('problem_count', models.IntegerField()),
                ('encounter_count', models.IntegerField()),
                ('document_count', models.IntegerField()),
            ],
            options={
                'db_table': 'vw_top_patients',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='EncounterMedication',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('encounter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medications', to='emr.Encounter')),
                ('medication', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='encounters', to='emr.Medication')),
            ],
            options={
                'db_table': 'emr_encounter_medication',
            },
        ),
    ]
