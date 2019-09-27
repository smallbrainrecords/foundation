# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('emr', '0039_remove_label_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('line1', models.CharField(max_length=50)),
                ('line2', models.CharField(max_length=50)),
                ('zip', models.CharField(max_length=6)),
                ('zip4', models.CharField(max_length=4, null=True, blank=True)),
                ('lat', models.DecimalField(null=True, max_digits=10, decimal_places=8, blank=True)),
                ('lon', models.DecimalField(null=True, max_digits=11, decimal_places=4, blank=True)),
                ('county', models.CharField(max_length=30, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AddressType',
            fields=[
                ('code', models.CharField(max_length=8, serialize=False, primary_key=True)),
                ('display', models.CharField(max_length=17)),
                ('definition', models.CharField(max_length=51)),
            ],
        ),
        migrations.CreateModel(
            name='AddressUse',
            fields=[
                ('code', models.CharField(max_length=4, serialize=False, primary_key=True)),
                ('display', models.CharField(max_length=15)),
                ('definition', models.CharField(max_length=90)),
            ],
        ),
        migrations.CreateModel(
            name='City',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('iso3', models.CharField(max_length=3)),
                ('iso_num', models.CharField(max_length=3)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='MaritalStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=1, null=True, blank=True)),
                ('display', models.CharField(max_length=20, null=True, blank=True)),
                ('definition', models.CharField(max_length=64, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Observation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(max_length=16)),
                ('category', models.CharField(max_length=45, null=True, blank=True)),
                ('code', models.CharField(max_length=10)),
                ('effective_datetime', models.DateTimeField(null=True, blank=True)),
                ('value_quantity', models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)),
                ('value_codeableconcept', models.CharField(max_length=40, null=True, blank=True)),
                ('value_string', models.TextField(null=True, blank=True)),
                ('value_unit', models.CharField(max_length=45, null=True, blank=True)),
                ('comments', models.TextField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_on'],
            },
        ),
        migrations.CreateModel(
            name='ObservationComponent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(max_length=16)),
                ('component_code', models.CharField(max_length=10)),
                ('value_quantity', models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)),
                ('value_codeableconcept', models.CharField(max_length=40, null=True, blank=True)),
                ('value_string', models.TextField(null=True, blank=True)),
                ('value_unit', models.CharField(max_length=45, null=True, blank=True)),
                ('comments', models.TextField(null=True, blank=True)),
                ('observation', models.ForeignKey(related_name='observation_components', to='emr.Observation')),
            ],
        ),
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=2)),
                ('name', models.CharField(max_length=50)),
                ('country', models.ForeignKey(related_name='country_states', to='emr.Country')),
            ],
        ),
        migrations.CreateModel(
            name='Telecom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('system_code', models.CharField(max_length=5)),
                ('value', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='TelecomSystem',
            fields=[
                ('code', models.CharField(max_length=5, serialize=False, primary_key=True)),
                ('display', models.CharField(max_length=50)),
                ('definition', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='UserAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateField(null=True, blank=True)),
                ('end', models.DateField(null=True, blank=True)),
                ('address', models.ForeignKey(related_name='address_users', to='emr.Address')),
                ('type_code', models.ForeignKey(related_name='type_code_user_address', to='emr.AddressType')),
                ('use_code', models.ForeignKey(related_name='use_code_user_address', to='emr.AddressUse')),
                ('user', models.ForeignKey(related_name='user_addresses', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserTelecom',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('use_code', models.CharField(max_length=6)),
                ('rank', models.PositiveIntegerField(null=True, blank=True)),
                ('start', models.DateField(null=True, blank=True)),
                ('end', models.DateField(null=True, blank=True)),
                ('telecom', models.ForeignKey(related_name='telecom_users', to='emr.Telecom')),
                ('user', models.ForeignKey(related_name='user_telecoms', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='userprofile',
            name='deceased_date',
            field=models.DateTimeField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='observation',
            name='author',
            field=models.ForeignKey(related_name='observation_authors', blank=True, to='emr.UserProfile', null=True),
        ),
        migrations.AddField(
            model_name='observation',
            name='encounter',
            field=models.ForeignKey(related_name='observation_encounters', blank=True, to='emr.UserProfile', null=True),
        ),
        migrations.AddField(
            model_name='observation',
            name='performer',
            field=models.ForeignKey(related_name='observation_performers', blank=True, to='emr.UserProfile', null=True),
        ),
        migrations.AddField(
            model_name='observation',
            name='subject',
            field=models.ForeignKey(related_name='observation_subjects', to='emr.UserProfile'),
        ),
        migrations.AddField(
            model_name='city',
            name='state',
            field=models.ForeignKey(related_name='state_cities', to='emr.State'),
        ),
        migrations.AddField(
            model_name='address',
            name='city',
            field=models.ForeignKey(related_name='city_addresses', to='emr.City'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='marital_status',
            field=models.ForeignKey(blank=True, to='emr.MaritalStatus', null=True),
        ),
    ]
