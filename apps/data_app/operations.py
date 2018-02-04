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
from emr.models import ObservationValue


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
