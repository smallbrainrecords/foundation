# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mptt.fields
from django.conf import settings
from django.db import models, migrations

import emr.models


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('summary', models.TextField()),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Encounter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('starttime', models.DateTimeField(auto_now_add=True)),
                ('stoptime', models.DateTimeField(null=True, blank=True)),
                ('audio', models.FileField(upload_to=emr.models.get_path, blank=True)),
                ('video', models.FileField(upload_to=emr.models.get_path, blank=True)),
                ('note', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='EncounterEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='EventSummary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('summary', models.TextField()),
                ('patient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Goal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('goal', models.TextField()),
                ('is_controlled', models.BooleanField(default=False)),
                ('accomplished', models.BooleanField(default=False)),
                ('start_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Guideline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('concept_id', models.CharField(max_length=20, blank=True)),
                ('guideline', models.TextField()),
                ('reference_url', models.CharField(max_length=400, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='GuidelineForm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('form', models.TextField()),
                ('guideline', models.OneToOneField(to='emr.Guideline')),
            ],
        ),
        migrations.CreateModel(
            name='PatientImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=emr.models.get_path)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('problem_name', models.CharField(max_length=200)),
                ('concept_id', models.CharField(max_length=20, blank=True)),
                ('is_controlled', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('authenticated', models.BooleanField(default=False)),
                ('start_date', models.DateField(auto_now_add=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProblemRelationship',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('source', models.ForeignKey(related_name='source', to='emr.Problem')),
                ('target', models.ForeignKey(related_name='target', to='emr.Problem')),
            ],
        ),
        migrations.CreateModel(
            name='Sharing',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('all', models.BooleanField(default=True)),
                ('other_patient', models.ForeignKey(related_name='other_patient', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(related_name='target_patient', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='TextNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('by',
                 models.CharField(max_length=20, choices=[(b'patient', b'patient'), (b'physician', b'physician')])),
                ('note', models.TextField()),
                ('datetime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ToDo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('todo', models.TextField()),
                ('accomplished', models.BooleanField(default=False)),
                ('notes', models.ManyToManyField(to='emr.TextNote', blank=True)),
                ('patient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('problem', models.ForeignKey(blank=True, to='emr.Problem', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(default=b'patient', max_length=10,
                                          choices=[(b'patient', b'patient'), (b'physician', b'physician'),
                                                   (b'admin', b'admin')])),
                ('data', models.TextField(blank=True)),
                ('cover_image', models.ImageField(upload_to=b'cover_image/', blank=True)),
                ('portrait_image', models.ImageField(upload_to=b'cover_image/', blank=True)),
                ('summary', models.TextField(blank=True)),
                ('sex',
                 models.CharField(blank=True, max_length=6, choices=[(b'male', b'male'), (b'female', b'female')])),
                ('date_of_birth', models.DateField(null=True, blank=True)),
                ('phone_number', models.CharField(max_length=20, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Viewer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('tracking_id', models.CharField(max_length=20, blank=True)),
                ('user_agent', models.CharField(max_length=200, blank=True)),
                ('patient', models.ForeignKey(related_name='viewed_patient', to=settings.AUTH_USER_MODEL)),
                ('viewer', models.ForeignKey(related_name='viewer', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ViewStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.TextField()),
                ('patient', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='problem',
            name='notes',
            field=models.ManyToManyField(to='emr.TextNote', blank=True),
        ),
        migrations.AddField(
            model_name='problem',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='emr.Problem', null=True),
        ),
        migrations.AddField(
            model_name='problem',
            name='patient',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='patientimage',
            name='problem',
            field=models.ForeignKey(blank=True, to='emr.Problem', null=True),
        ),
        migrations.AddField(
            model_name='goal',
            name='notes',
            field=models.ManyToManyField(to='emr.TextNote', blank=True),
        ),
        migrations.AddField(
            model_name='goal',
            name='patient',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='goal',
            name='problem',
            field=models.ForeignKey(blank=True, to='emr.Problem', null=True),
        ),
        migrations.AddField(
            model_name='encounter',
            name='events',
            field=models.ManyToManyField(to='emr.EncounterEvent', blank=True),
        ),
        migrations.AddField(
            model_name='encounter',
            name='patient',
            field=models.ForeignKey(related_name='patient', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='encounter',
            name='physician',
            field=models.ForeignKey(related_name='physician', to=settings.AUTH_USER_MODEL),
        ),
    ]
