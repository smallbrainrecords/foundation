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
from document_app.views import *

urlpatterns = [
    re_path(r"^$", get_document_list),
    re_path(r"^upload_document$", upload_document),
    re_path(r"^info/(?P<document_id>\d+)$", document_info),
    re_path(r"^pin/patient$", pin_patient_2_document),
    re_path(r"^pin/label$", pin_label_2_document),
    re_path(r"^remove/label$", remove_document_label),
    re_path(r"^pin/todo$", pin_todo_2_document),
    re_path(r"^unpin/todo$", unpin_document_todo),
    re_path(r"^pin/problem$", pin_problem_2_document),
    re_path(r"^unpin/problem$", unpin_document_problem),
    re_path(r"^search_patient$", search_patient),
    re_path(r"^(?P<patient_id>\d+)/get_pinned_document$", get_patient_document),
    re_path(r"^delete/(?P<document_id>\d+)$", delete_document),
    re_path(r"^remove/(?P<document_id>\d+)$", remove_document),
    re_path(r"^(?P<document_id>\d+)/name$", update_name),
]
