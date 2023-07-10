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
from encounters_app.views import *

urlpatterns = [
    re_path(
        r"^patient/(?P<patient_id>\d+)/encounter/status$", patient_encounter_status
    ),
    re_path(r"^patient/(?P<patient_id>\d+)/encounter/start$", create_new_encounter),
    re_path(
        r"^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/update_note$",
        update_encounter_note,
    ),
    re_path(
        r"^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/upload_video/$",
        upload_encounter_video,
    ),
    re_path(
        r"^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/upload_audio/$",
        upload_encounter_audio,
    ),
    re_path(
        r"^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/add_timestamp$",
        add_timestamp,
    ),
    re_path(
        r"^patient/(?P<patient_id>\d+)/encounter/(?P<encounter_id>\d+)/delete$",
        delete_encounter,
    ),
    re_path(r"^encounter/(?P<encounter_id>\d+)/stop$", stop_patient_encounter),
    re_path(r"^encounter/(?P<encounter_id>\d+)/info$", get_encounter_info),
    re_path(
        r"^encounter/(?P<encounter_id>\d+)/recorder_status$", toggle_encounter_recorder
    ),
    re_path(
        r"^encounter/(?P<encounter_id>\d+)/audio_played$", increase_audio_played_count
    ),
    re_path(r"^encounter/(?P<encounter_id>\d+)/event$", add_encounter_event),
    re_path(r"^encounter/add/event_summary$", add_event_summary),
    re_path(
        r"^encounter_event/(?P<encounter_event_id>\d+)/mark_favorite$", mark_favorite
    ),
    re_path(
        r"^encounter_event/(?P<encounter_event_id>\d+)/name_favorite$", name_favorite
    ),
]
