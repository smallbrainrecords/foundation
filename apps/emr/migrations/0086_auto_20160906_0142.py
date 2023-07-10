# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0085_observationfield_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='ObservationValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.CharField(max_length=16, null=True, blank=True)),
                ('value_quantity', models.DecimalField(null=True, max_digits=10, decimal_places=4, blank=True)),
                ('value_codeableconcept', models.CharField(max_length=40, null=True, blank=True)),
                ('value_string', models.TextField(null=True, blank=True)),
                ('value_unit', models.CharField(max_length=45, null=True, blank=True)),
                ('effective_datetime', models.DateTimeField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('author', models.ForeignKey(related_name='observation_value_authors', blank=True, to='emr.UserProfile',
                                             null=True, on_delete=models.DO_NOTHING)),
            ],
        ),
        migrations.RemoveField(
            model_name='observationfield',
            name='observation',
        ),
        migrations.RemoveField(
            model_name='observationcomponent',
            name='field',
        ),
        migrations.AddField(
            model_name='observationcomponent',
            name='name',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.DeleteModel(
            name='ObservationField',
        ),
        migrations.AddField(
            model_name='observationvalue',
            name='component',
            field=models.ForeignKey(related_name='observation_component_values', to='emr.ObservationComponent', on_delete=models.DO_NOTHING),
        ),
    ]
