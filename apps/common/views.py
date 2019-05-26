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
import functools
import json
import time
from datetime import datetime

from django.http import *

from emr.manage_patient_permissions import check_permissions
from emr.models import ObservationComponent


def ajax_response(resp):
    return HttpResponse(json.dumps(resp), content_type="application/json")


def get_date(date_string):
    try:
        date_object = datetime.strptime(date_string, "%Y-%m-%d").date()
        return date_object
    except:
        return "Unsupported format"

def get_new_date(date_string):
    return datetime.strptime(date_string, "%m/%d/%Y").date()


def permissions_required(permissions):
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapper(request, *args, **kwargs):
            actor_profile, permitted = check_permissions(permissions, request.user)
            if not permitted:
                resp = {'success': False}
                return ajax_response(resp)
            return view_func(request, *args, **kwargs)

        return _wrapper

    return decorator


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('Time it: %r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te - ts))
        return result

    return timed


def validate_effective_datetime(date_text):
    """
    Validate date effective date time format %m/%d/%Y %H:%M
    :param date_text:
    :return:
    """
    try:
        datetime.strptime(date_text, '%m/%d/%Y %H:%M')
        return True
    except ValueError:
        return False


def validate_number(number_text):
    try:
        float(number_text)
        return True
    except ValueError:
        return False


def validate_value_quantity(component_id, value_quantity):
    try:
        observation_component = ObservationComponent.objects.get(id=component_id)
        if '55757-9' == observation_component.component_code:
            return 0 <= int(value_quantity) <= 6

        return True
    except ValueError:
        return False
