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

from colons_app.views import *
from django.urls import re_path

urlpatterns = [
    re_path(r"^(?P<colon_id>\d+)/info$", get_colon_info),
    re_path(r"^(?P<colon_id>\d+)/refuse$", refuse),
    re_path(r"^(?P<colon_id>\d+)/not_appropriate$", not_appropriate),
    re_path(r"^study/(?P<study_id>\d+)/info$", get_study_info),
    re_path(r"^(?P<colon_id>\d+)/add_study$", add_study),
    re_path(r"^(?P<study_id>\d+)/edit_study$", edit_study),
    re_path(r"^(?P<study_id>\d+)/delete_study$", delete_study),
    re_path(r"^study/(?P<study_id>\d+)/upload_image$", upload_study_image),
    re_path(r"^study/(?P<study_id>\d+)/addImage$", add_study_image),
    re_path(
        r"^study/(?P<study_id>\d+)/image/(?P<image_id>\d+)/delete$", delete_study_image
    ),
    re_path(r"^(?P<colon_id>\d+)/add_factor$", add_factor),
    re_path(r"^(?P<colon_id>\d+)/delete_factor$", delete_factor),
    re_path(r"^(?P<colon_id>\d+)/add_note$", add_note),
    re_path(r"^note/(?P<note_id>\d+)/edit$", edit_note),
    re_path(r"^note/(?P<note_id>\d+)/delete$", delete_note),
    re_path(r"^(?P<colon_id>\d+)/track/click$", track_colon_click),
    # new restURL
    re_path(r"^(?P<colon_id>\d+)$", get_colon_info),
    re_path(r"^(?P<colon_id>\d+)/studies$", get_colon_cancer_studies),
    re_path(r"^(?P<colon_id>\d+)/studies/(?P<study_id>\d+)$", colon_cancer_study),
    re_path(r"^(?P<colon_id>\d+)/risk-factors$", get_risk_factors),
    re_path(r"^(?P<colon_id>\d+)/risk-factors/(?P<risk_factor_id>\d+)$", risk_factor),
    re_path(r"^(?P<colon_id>\d+)/notes$", get_notes),
    re_path(r"^(?P<colon_id>\d+)/notes/(?P<note_id>\d+)$", note),
]
