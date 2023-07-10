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
from medication_app.views import *

urlpatterns = [
    re_path(r"^list_terms$", list_terms),
    re_path(r"^note/(?P<note_id>\d+)/edit$", edit_note),
    re_path(r"^note/(?P<note_id>\d+)/delete$", delete_note),
    re_path(r"^(?P<patient_id>\d+)/pin_to_problem$", pin_to_problem),
    re_path(r"^(?P<patient_id>\d+)/get_medications$", get_medications),
    re_path(r"^(?P<patient_id>\d+)/add_medication$", add_medication),
    re_path(
        r"^(?P<patient_id>\d+)/(?P<medication_id>\d+)/change_active_medication$",
        change_active_medication,
    ),
    re_path(
        r"^(?P<patient_id>\d+)/(?P<medication_id>\d+)/change_dosage$", change_dosage
    ),
    re_path(
        r"^(?P<patient_id>\d+)/(?P<medication_id>\d+)/access$", on_medication_accessed
    ),
    re_path(
        r"^(?P<patient_id>\d+)/(?P<medication_id>\d+)/add_medication_note$",
        add_medication_note,
    ),
    re_path(
        r"^(?P<patient_id>\d+)/medication/(?P<medication_id>\d+)/info$", get_medication
    ),
    re_path(r"^(?P<medication_id>\d+)/get_pins$", get_pins),
    re_path(r"^(?P<medication_id>\d+)/encounters$", get_medication_encounter),
]
