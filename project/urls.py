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
import debug_toolbar
import django
from django.conf.urls import include
from django.contrib.auth import views
from django.urls import path, re_path

from apps.a1c_app import urls as a1c_app_urls
from apps.colons_app import urls as colons_app_urls
from apps.data_app import urls as data_app_urls
from apps.document_app import urls
from apps.document_app import urls as document_app_urls
from apps.emr import views as emr_views
from apps.emr.views import LoginError
from apps.encounters_app import urls as encounters_app_urls
from apps.goals_app import urls as goals_app_urls
from apps.inr_app import urls as inr_app_urls
from apps.medication_app import urls as medication_app_urls
from apps.my_story_app import urls as my_story_app_urls
from apps.pain import views as pain_views
from apps.problems_app import urls as problems_app_urls
from apps.project_admin_app import urls as project_admin_app_urls
from apps.todo_app import urls as todo_app_urls
from apps.users_app import urls as users_app_urls

# import settings
from project import settings
from project.views import home

# from genericadmin.admin import *




# admin.autodiscover()

urlpatterns = [
    path('__debug__/', include(debug_toolbar.urls)),
    re_path(r'^$', home,name='project_home'),

    # re_path(r'^admin/', include(admin.site.urls)),

    re_path(r'^project/admin/', include(project_admin_app_urls)),

    re_path(r'^pain/create_pain_avatar/(?P<patient_id>\d+)/$', pain_views.create_pain_avatar),
    re_path(r'^pain/reset/$', pain_views.reset),
    re_path(r'^login-error/$', LoginError.as_view()),

    # Old user views
    re_path(r'^logout/$', django.contrib.auth.views.LogoutView.as_view(), {'next_page': '/'}),

    # Old views
    re_path(r'^list_of_unregistered_users/$', emr_views.list_of_unregistered_users),
    re_path(r'^register_users/$', emr_views.register_users),
    re_path(r'^list_of_users/$', emr_views.list_users),

    re_path(r'^get_problems/(?P<patient_id>\d+)/$', emr_views.get_patient_data),
    re_path(r'^change_status/$', emr_views.change_status),
    re_path(r'^patient/(?P<patient_id>\d+)/add_problem/$', emr_views.add_problem),
    re_path(r'^add_patient_summary/(?P<patient_id>\d+)/$', emr_views.save_patient_summary),

    re_path(r'^update/$', emr_views.update),

    # New URLS
    re_path(r'^list_terms/$', emr_views.list_snomed_terms),

    # Users
    re_path(r'^u/', include(users_app_urls)),

    # Problems
    re_path(r'^p/', include(problems_app_urls)),

    # Goals
    re_path(r'^g/', include(goals_app_urls)),

    # Encounters
    re_path(r'^enc/', include(encounters_app_urls)),

    # Todos
    re_path(r'^todo/', include(todo_app_urls)),

    # Observations
    re_path(r'^a1c/', include(a1c_app_urls)),

    # colon cancer
    re_path(r'^colon_cancer/', include(colons_app_urls)),

    # my story
    re_path(r'^my_story/', include(my_story_app_urls)),

    # data
    re_path(r'^data/', include(data_app_urls)),

    # inr
    re_path(r'^inr/', include(inr_app_urls)),
    re_path(r'^medication/', include(medication_app_urls)),

    # document
    re_path(r'^docs/', include(document_app_urls)),

    # Pain Avatars
    re_path(r'^patient/(?P<patient_id>\d+)/pain_avatars$', pain_views.patient_pain_avatars),
    re_path(r'^patient/(?P<patient_id>\d+)/pain/add_pain_avatar$', pain_views.add_pain_avatar),

    re_path(r'session_security/', include('session_security.urls')),

    # MEDIA AND STATIC FILES
    re_path(r'^media/(?P<path>.*)$', emr_views.serve_private_file),
    re_path(r'^static/(?P<path>.*)$', django.views.static.serve,
        {'document_root': settings.STATIC_ROOT, 'show_indexes': True})
]
