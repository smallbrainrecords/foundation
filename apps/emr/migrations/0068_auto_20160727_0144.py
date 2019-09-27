# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0067_coloncancerscreening'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColonCancerStudy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('study_date', models.DateField(null=True, blank=True)),
                ('finding', models.CharField(default=b'fecal occult blood test', max_length=100,
                                             choices=[(b'fecal occult blood test', b'Fecal occult blood test'),
                                                      (b'colonoscopy', b'Colonoscopy'),
                                                      (b'fecal immunochemical test', b'Fecal immunochemical test'),
                                                      (b'other', b'Other')])),
                ('result', models.CharField(max_length=100, null=True, blank=True)),
                ('note', models.TextField(null=True, blank=True)),
                ('last_updated_date', models.DateField(auto_now=True)),
                ('author', models.ForeignKey(related_name='author_studies', to='emr.UserProfile')),
                ('colon', models.ForeignKey(related_name='colon_studies', to='emr.ColonCancerScreening')),
                (
                'last_updated_user', models.ForeignKey(related_name='last_updated_user_studies', to='emr.UserProfile')),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
        migrations.CreateModel(
            name='ColonCancerStudyImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=b'studies/', blank=True)),
            ],
        ),
        migrations.AddField(
            model_name='coloncancerstudy',
            name='report_images',
            field=models.ManyToManyField(related_name='report_images_studies', to='emr.ColonCancerStudyImage',
                                         blank=True),
        ),
    ]
