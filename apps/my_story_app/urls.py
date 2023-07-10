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
from my_story_app.views import *

urlpatterns = [
    re_path(r"^track/click$", track_tab_click),
    re_path(r"^(?P<patient_id>\d+)/get_my_story$", get_my_story),
    re_path(r"^(?P<tab_id>\d+)/info$", get_tab_info),
    re_path(r"^(?P<patient_id>\d+)/add_tab$", add_tab),
    re_path(r"^(?P<patient_id>\d+)/(?P<tab_id>\d+)/add_text$", add_text),
    re_path(r"^(?P<patient_id>\d+)/delete_tab/(?P<tab_id>\d+)$", delete_tab),
    re_path(r"^(?P<patient_id>\d+)/save_tab/(?P<tab_id>\d+)$", save_tab),
    re_path(
        r"^(?P<patient_id>\d+)/delete_text_component/(?P<component_id>\d+)$",
        delete_text_component,
    ),
    re_path(
        r"^(?P<patient_id>\d+)/save_text_component/(?P<component_id>\d+)$",
        save_text_component,
    ),
    re_path(
        r"^(?P<patient_id>\d+)/save_text_component_entry/(?P<component_id>\d+)$",
        save_text_component_entry,
    ),
]
