from django.shortcuts import render 
from django.shortcuts import render_to_response
from django.db.models.loading import get_model
from django.http import HttpResponse, HttpResponseRedirect




from django.http import *
from django.shortcuts import redirect
from django.template import RequestContext

from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from django.contrib.auth.decorators import user_passes_test


from datetime import datetime, timedelta
import os, json

import traceback
import functools


from django.contrib.contenttypes.models import ContentType



from django.core.urlresolvers import reverse
from django.contrib import messages

from django.views.generic.base import View
from social_auth.exceptions import AuthFailed
from social_auth.views import complete

from django.core import serializers

from django.db.models import Q
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