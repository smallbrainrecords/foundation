# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import connection
from django.db import migrations

from emr.models import ObservationValue, ObservationComponent


def fix_blood_glitch(apps, schema_editor):
    """
    Do adding missing blood pressure value
    :return:
    """
    blood_pressure_components = get_blood_pressure_obs_component_ids()

    # For each component pairing
    for pair in blood_pressure_components:
        results = get_observation_value_pair(pair['component_ids'])
        for result in results:
            if result['no_of_component'] == 1:
                value = ObservationValue.objects.filter(id=result['existed_value_ids']).get()
                missing_component = pair['component_ids'].replace(result['existed_component_ids'], '').replace(",", "")

                obs = ObservationValue.objects.create(
                    component=ObservationComponent.objects.filter(id=int(missing_component)).get(),
                    value_quantity=0,
                    author=value.author,
                    effective_datetime=value.effective_datetime
                )
                obs.created_on = value.created_on
                obs.save()


def get_blood_pressure_obs_component_ids():
    """

    :return:
    """
    raw_query = "SELECT group_concat(id SEPARATOR ',') AS component_ids FROM emr_observationcomponent WHERE name IN ('systolic','diastolic')  GROUP BY observation_id"

    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        columns = [col[0] for col in cursor.description]
        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


def get_observation_value_pair(component_id):
    """

    :param component_id:
    :return:
    """
    raw_query = "SELECT  COUNT('component_id') AS no_of_component, DATE_FORMAT(created_on, '%m/%d/%Y %H:%i') AS entry_time,  GROUP_CONCAT(id SEPARATOR '&') AS existed_value_ids, GROUP_CONCAT(component_id SEPARATOR ',') AS existed_component_ids FROM emr_observationvalue WHERE component_id IN ({0}) GROUP BY DATE_FORMAT(created_on, '%Y-%m-%d %H:%i:%s') ORDER  BY COUNT(component_id)" \
        .format(component_id)
    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        columns = [col[0] for col in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0162_auto_20180624_1203'),
    ]

    operations = [
        migrations.RunPython(fix_blood_glitch)
    ]
