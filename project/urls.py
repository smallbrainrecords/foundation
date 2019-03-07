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
import django
import session_security
from django import contrib, views
from django.conf.urls import include
from django.contrib import auth
from django.contrib.auth import views
from django.views import static
from genericadmin.admin import *
from session_security import urls

import a1c_app
import colons_app
import data_app
import document_app
import emr
import encounters_app
import goals_app
import inr_app
import medication_app
import my_story_app
import pain
import problems_app
import project_admin_app
import settings
import todo_app
import users_app
from a1c_app import urls
from colons_app import urls
from data_app import urls
from document_app import urls
from emr import views
from emr.views import LoginError
from encounters_app import urls
from goals_app import urls
from inr_app import urls
from medication_app import urls
from my_story_app import urls
from pain import views
from problems_app import urls
from project_admin_app import urls
from todo_app import urls
from users_app import urls
from views import home

admin.autodiscover()

urlpatterns = [
    url(r'^$', home),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^project/admin/', include(project_admin_app.urls)),

    url(r'^pain/create_pain_avatar/(?P<patient_id>\d+)/$', pain.views.create_pain_avatar),
    url(r'^pain/reset/$', pain.views.reset),
    url(r'^login-error/$', LoginError.as_view()),

    # Old user views
    url(r'^logout/$', django.contrib.auth.views.logout, {'next_page': '/'}),

    # Old views
    url(r'^list_of_unregistered_users/$', emr.views.list_of_unregistered_users),
    url(r'^register_users/$', emr.views.register_users),
    url(r'^list_of_users/$', emr.views.list_users),

    url(r'^get_problems/(?P<patient_id>\d+)/$', emr.views.get_patient_data),
    url(r'^change_status/$', emr.views.change_status),
    url(r'^patient/(?P<patient_id>\d+)/add_problem/$', emr.views.add_problem),
    url(r'^add_patient_summary/(?P<patient_id>\d+)/$', emr.views.save_patient_summary),

    url(r'^update/$', emr.views.update),

    # New URLS
    url(r'^list_terms/$', emr.views.list_snomed_terms),

    # Users
    url(r'^u/', include(users_app.urls)),

    # Problems
    url(r'^p/', include(problems_app.urls)),

    # Goals
    url(r'^g/', include(goals_app.urls)),

    # Encounters
    url(r'^enc/', include(encounters_app.urls)),

    # Todos
    url(r'^todo/', include(todo_app.urls)),

    # Observations
    url(r'^a1c/', include(a1c_app.urls)),

    # colon cancer
    url(r'^colon_cancer/', include(colons_app.urls)),

    # my story
    url(r'^my_story/', include(my_story_app.urls)),

    # data
    url(r'^data/', include(data_app.urls)),

    # inr
    url(r'^inr/', include(inr_app.urls)),
    url(r'^medication/', include(medication_app.urls)),

    # document
    url(r'^docs/', include(document_app.urls)),

    # Pain Avatars
    url(r'^patient/(?P<patient_id>\d+)/pain_avatars$', pain.views.patient_pain_avatars),
    url(r'^patient/(?P<patient_id>\d+)/pain/add_pain_avatar$', pain.views.add_pain_avatar),

    url(r'session_security/', include(session_security.urls)),

    # MEDIA AND STATIC FILES
    url(r'^media/(?P<path>.*)$', emr.views.serve_private_file),
    url(r'^static/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.STATIC_ROOT, 'show_indexes': True})
]
