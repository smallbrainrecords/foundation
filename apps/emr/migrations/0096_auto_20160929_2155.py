# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0095_auto_20160926_2235'),
    ]

    operations = [
        migrations.CreateModel(
            name='Inr',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(related_name='patient_inr', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
        migrations.CreateModel(
            name='InrValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)),
                ('effective_datetime', models.DateTimeField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(related_name='author_inr_values', to='emr.UserProfile')),
                ('inr', models.ForeignKey(related_name='inr_values', to='emr.Inr')),
            ],
            options={
                'ordering': ['-effective_datetime', '-created_on'],
            },
        ),
        migrations.CreateModel(
            name='Medication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.TextField(null=True, blank=True)),
                ('concept_id', models.CharField(max_length=20, null=True, blank=True)),
                ('current', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(related_name='author_medications', to='emr.UserProfile')),
                ('inr', models.ForeignKey(related_name='inr_medications', to='emr.Inr')),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
        migrations.CreateModel(
            name='MedicationPinToProblem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('author', models.ForeignKey(related_name='author_pin_medications', blank=True, to='emr.UserProfile', null=True)),
                ('medication', models.ForeignKey(related_name='medication_pin_medications', to='emr.Medication')),
                ('problem', models.ForeignKey(related_name='problem_pin_medications', to='emr.Problem')),
            ],
        ),
        migrations.CreateModel(
            name='MedicationTextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(to='emr.UserProfile')),
                ('medication', models.ForeignKey(related_name='medication_notes', to='emr.Medication')),
            ],
        ),
        migrations.AlterModelOptions(
            name='observationvalue',
            options={'ordering': ['effective_datetime', 'created_on']},
        ),
        migrations.AddField(
            model_name='todo',
            name='inr',
            field=models.ForeignKey(related_name='inr_todos', blank=True, to='emr.Inr', null=True),
        ),
    ]
