# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('emr', '0119_userprofile_last_access_tagged_todo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='cover_image',
            field=models.ImageField(default=b'/static/images/cover.png', upload_to=b'cover_image/'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='last_access_tagged_todo',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='portrait_image',
            field=models.ImageField(default=b'/static/images/avatar.png', upload_to=b'cover_image/'),
        ),
    ]
