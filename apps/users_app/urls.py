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

# from django.conf.urls import url
from django.urls import re_path
from users_app.views import *

urlpatterns = [
    re_path(r'^login/$', login_user),
    re_path(r'^logout/$', logout_user),
    re_path(r'^register/$', register_user),
    re_path(r'^home/$', home),
    re_path(r'^staff/$', staff),
    re_path(r'^staff/search$', staff_search, name="staff_search"),
    re_path(r'^patient/manage/(?P<user_id>\d+)/search$', search, name="search"),
    re_path(r'^patient/manage/(?P<user_id>\d+)/$', manage_patient),
    re_path(r'^patient/(?P<patient_id>\d+)/info$', get_patient_info),
    re_path(r'^patient/(?P<patient_id>\d+)/timelineinfo$', get_timeline_info),
    re_path(r'^patient/(?P<patient_id>\d+)/patient_todos_info$', get_patient_todos_info),
    re_path(r'^user_info/(?P<user_id>\d+)/info/$', user_info),
    re_path(r'^patient/(?P<patient_id>\d+)/profile/update_summary$', update_patient_summary),
    re_path(r'^patient/(?P<patient_id>\d+)/profile/update_password$', update_patient_password),
    re_path(r'^patient/(?P<patient_id>\d+)/update/basic$', update_basic_profile),
    re_path(r'^patient/(?P<patient_id>\d+)/update/profile$', update_profile),
    re_path(r'^patient/(?P<patient_id>\d+)/update/email$', update_patient_email),
    re_path(r'^active/user/$', fetch_active_user),
    re_path(r'^members/(?P<user_id>\d+)/getlist/$', get_patient_members),
    re_path(r'^patients/$', get_patients_list),
    re_path(r'^patient/add_sharing_patient/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)$',
        add_sharing_patient),
    re_path(r'^patient/remove_sharing_patient/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)$',
        remove_sharing_patient),
    re_path(r'^patient/change_sharing_my_story/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)$',
        change_sharing_my_story),
    re_path(r'^sharing_patients/(?P<patient_id>\d+)$', get_sharing_patients),
    re_path(r'^patient/(?P<patient_id>\d+)/profile/update_note$', update_patient_note),
    re_path(r'^todos_physicians/(?P<user_id>\d+)$', get_todos_physicians),
    re_path(r'^(?P<user_id>\d+)/profile/last_access_tagged_todo$', update_last_access_tagged_todo),
    re_path(r'^setting$', get_general_setting),
    re_path(r'^update_setting$', update_general_setting),

    # URL for API patterns
    re_path(r'^users/(?P<patient_id>\d+)/problems$', get_user_problem),
    re_path(r'^users/(?P<patient_id>\d+)/todos$', get_user_todo),
    re_path(r'^users/(?P<patient_id>\d+)/vitals$', get_user_vitals),
    re_path(r'^users/(?P<patient_id>\d+)/medicare$', set_user_medicare),
    re_path(r'^users/(?P<user_id>\d+)/cover$', cover),

    # GET most recent encounter
    re_path(r'^users/(?P<patient_id>\d+)/encounters$', get_most_recent_encounter),

    re_path(r'^users/(?P<patient_id>\d+)/add_narratives$', add_narratives),
    re_path(r'^users/(?P<patient_id>\d+)/narratives$', get_user_narratives),
    re_path(r'^users/(?P<patient_id>\d+)/get_all_narratives$', get_all_narratives),
]
