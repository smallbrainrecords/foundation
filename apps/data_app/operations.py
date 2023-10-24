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
from datetime import datetime

from django.db import connection, transaction
from emr.models import ObservationComponent, ObservationValue
from emr.operations import op_add_event


# @timeit
def get_observation_most_common_value(component):
    """
    Get most recent value of observation component
    :param component:
    :param effective_datetime:
    :return:
    """
    most_recent_value = (
        ObservationValue.objects.using("default_read_uncommitted")
        .filter(component=component)
        .order_by("-effective_datetime")
    )
    if most_recent_value.exists():
        return float(most_recent_value.first().value_quantity)
    else:
        return None


# @timeit
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


# @timeit
def get_observation_value_pair(component_id):
    """

    :param component_id:
    :return:
    """
    raw_query = "SELECT DATE_FORMAT(ANY_VALUE(created_on), '%m/%d/%Y %H:%i') as entry_time, GROUP_CONCAT(ANY_VALUE(value_quantity) SEPARATOR '/') as value,  GROUP_CONCAT(ANY_VALUE(id) SEPARATOR '&') as edit_link FROM emr_observationvalue WHERE component_id IN ({0}) GROUP BY DATE_FORMAT(created_on, '%Y-%m-%d %H:%i:%s')".format(
        component_id
    )
    with connection.cursor() as cursor:
        cursor.execute(raw_query)
        columns = [col[0] for col in cursor.description]

        return [dict(zip(columns, row)) for row in cursor.fetchall()]


def handle_bmi_calculation(userProfile, request, value, patient, effective_datetime):
    if value.component.name == "weight":
        handle_weight_provided_event(
            value, userProfile, request, patient, effective_datetime
        )
    elif value.component.name == "height":
        handle_height_provided_event(
            value, userProfile, request, patient, effective_datetime
        )


def handle_weight_provided_event(
    value, userProfile, request, patient, effective_datetime
):
    heightComponent = (
        ObservationComponent.objects.filter(component_code="8302-2")
        .filter(observation__subject_id=int(patient.id))
        .get()
    )
    height = get_observation_most_common_value(heightComponent)

    if height is not None:
        bmiComponent = get_bmi_component(patient)
        bmiValue = calculate_bmi(value.value_quantity, height)
        ObservationValue(
            author=request.user,
            component=bmiComponent,
            effective_datetime=effective_datetime,
            value_quantity=bmiValue,
        ).save()

        if (
            userProfile.weight_updated_date == None
            or userProfile.weight_updated_date.date() < datetime.now().date()
        ):
            userProfile.weight_updated_date = datetime.now()
            userProfile.save()

        save_log(value, bmiComponent, request, bmiValue)
    else:
        pass


def handle_height_provided_event(
    value, userProfile, request, patient, effective_datetime
):
    weightComponent = (
        ObservationComponent.objects.filter(component_code="3141-9")
        .filter(observation__subject_id=int(patient.id))
        .get()
    )
    weight = get_observation_most_common_value(weightComponent)
    if weight is not None:
        bmiComponent = get_bmi_component(patient)
        bmiValue = calculate_bmi(weight, value.value_quantity)
        ObservationValue(
            author=request.user,
            component=bmiComponent,
            effective_datetime=effective_datetime,
            value_quantity=bmiValue,
        ).save()

        if userProfile.height_changed_first_time == False:
            userProfile.height_changed_first_time = True
            userProfile.height_updated_date = datetime.now()
            userProfile.save()
        else:
            if userProfile.height_updated_date.date() < datetime.now().date():
                userProfile.height_updated_date = datetime.now()
                userProfile.save()

        save_log(value, bmiComponent, request, bmiValue)

    else:
        pass


def get_bmi_component(patient):
    return (
        ObservationComponent.objects.filter(component_code="39156-5")
        .filter(observation__subject=patient)
        .first()
    )


def save_log(value, bmiComponent, request, bmiValue):
    # Save log
    summary = "A value of <b>{0}</b> was added for <b>{1}</b>".format(
        bmiValue, bmiComponent.observation.name
    )
    op_add_event(request.user, value.component.observation.subject, summary)


def calculate_bmi(weight_lbs, height_inches):
    # Convert pounds to kilograms (1 lb = 0.453592 kg)
    weight_kg = weight_lbs * 0.453592

    # Convert inches to meters (1 inch = 0.0254 meters)
    height_m = height_inches * 0.0254

    bmi = weight_kg / (height_m**2)
    rounded_bmi = round(bmi, 1)
    return rounded_bmi
