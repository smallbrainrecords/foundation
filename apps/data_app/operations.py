"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from common.views import timeit
from django.db import connection
from emr.models import ObservationValue


@timeit
def get_observation_most_common_value(component, effective_datetime):
    """
    Get most recent value of observation component
    :param component:
    :param effective_datetime:
    :return: 
    """
    observation_component = ObservationValue.objects.filter(component=component).filter(
        effective_datetime=effective_datetime)

    if observation_component.exists():
        return float(observation_component.first().value_quantity)
    else:
        most_recent_value = ObservationValue.objects.filter(component=component).order_by('-effective_datetime')
        if most_recent_value.exists():
            return float(most_recent_value.first().value_quantity)
        else:
            return float(1)


@timeit
def query_to_dicts(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(zip(col_names, row))
        yield row_dict
    return


@timeit
def get_observation_value_pair(component_id):
    """

    :param component_id:
    :return:
    """
    raw_query = "SELECT DATE_FORMAT(ANY_VALUE(created_on), '%m/%d/%Y %H:%i') as entry_time, GROUP_CONCAT(ANY_VALUE(value_quantity) SEPARATOR '/') as value,  GROUP_CONCAT(ANY_VALUE(id) SEPARATOR '&') as edit_link FROM emr_observationvalue WHERE component_id IN ({0}) GROUP BY DATE_FORMAT(created_on, '%Y-%m-%d %H:%i:%s')" \
        .format(component_id)
    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        columns = [col[0] for col in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
