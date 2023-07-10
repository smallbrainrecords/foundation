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
from django.urls import re_path
from goals_app.views import *

urlpatterns = [
    re_path(r"^goal/(?P<goal_id>\d+)/info$", get_goal_info),
    re_path(r"^patient/(?P<patient_id>\d+)/goals/add/new_goal$", add_patient_goal),
    re_path(
        r"^patient/(?P<patient_id>\d+)/goal/(?P<goal_id>\d+)/add_note$", add_goal_note
    ),
    re_path(
        r"^patient/(?P<patient_id>\d+)/goal/(?P<goal_id>\d+)/update_status$",
        update_goal_status,
    ),
    re_path(
        r"^patient/(?P<patient_id>\d+)/goal/(?P<goal_id>\d+)/change_name$", change_name
    ),
]
