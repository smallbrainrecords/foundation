import functools
import json
import time
from datetime import datetime

from django.http import *

from emr.manage_patient_permissions import check_permissions


def ajax_response(resp):

	return HttpResponse(json.dumps(resp), content_type="application/json" )


def get_date(date_string):
	return datetime.strptime(date_string, "%Y-%m-%d").date()

def get_new_date(date_string):
	return datetime.strptime(date_string, "%m/%d/%Y").date()

def permissions_required(permissions):
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapper(request, *args, **kwargs):
            actor_profile, permitted = check_permissions(permissions, request.user)
            if not permitted:
                resp = {}
                resp['success'] = False
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
