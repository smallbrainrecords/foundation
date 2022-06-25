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
from django.conf.urls import url

from project_admin_app.views import *

urlpatterns = [

    url(r'^$', home, name='pa_home'),

    url(r'^list/registered/users/$', list_registered_users,
        name='pa_list_registered_users'),

    url(r'^list/unregistered/users/$', list_unregistered_users,
        name='pa_list_unregistered_users'),

    url(r'^user/(?P<user_id>\d+)/info/$', user_info, name='pa_user_info'),

    url(r'^user/approve/$', approve_user, name='pa_approve_user'),

    url(r'^user/reject/$', reject_user, name='pa_reject_user'),

    url(r'^user/update/profile/$', update_profile, name='pa_update_profile'),

    url(r'^user/update/basic/$', update_basic_profile,
        name='pa_update_basic_profile'),

    url(r'^user/update/email/$', update_email, name='pa_update_email'),

    url(r'^user/update/password/$', update_password, name='pa_update_password'),

    url(r'^user/update/active/$', update_active, name='pa_update_active'),

    url(r'^user/update/deceased_date/$',
        update_deceased_date, name='pa_update_deceased_date'),

    url(r'^user/create/$', create_user, name='pa_create_user'),

    url(r'^patient/physicians/$', list_patient_physicians,
        name='pa_list_patient_physicians'),

    url(r'^assigned/physicians/$', list_assigned_physicians,
        name='pa_list_assigned_physicians'),

    url(r'^physician/data/$', fetch_physician_data,
        name='pa_fetch_physician_data'),

    url(r'^physician/team/$', get_physician_team,
        name='pa_fetch_physician_data'),

    url(r'^physician/patients/$', get_physician_patients,
        name='pa_fetch_physician_data'),

    url(r'^physician/assign/member/$', assign_physician_member,
        name='pa_assign_physician_member'),

    url(r'^physician/unassign/member/$', unassign_physician_member,
        name='pa_unassign_physician_member')
]
