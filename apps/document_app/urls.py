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

from document_app.views import *

urlpatterns = [
    url(r'^$', get_document_list),
    url(r'^upload_document$', upload_document),
    url(r'^info/(?P<document_id>\d+)$', document_info),
    url(r'^pin/patient$', pin_patient_2_document),
    url(r'^pin/label$', pin_label_2_document),
    url(r'^remove/label$', remove_document_label),
    url(r'^pin/todo$', pin_todo_2_document),
    url(r'^unpin/todo$', unpin_document_todo),
    url(r'^pin/problem$', pin_problem_2_document),
    url(r'^unpin/problem$', unpin_document_problem),
    url(r'^search_patient$', search_patient),
    url(r'^(?P<patient_id>\d+)/get_pinned_document$', get_patient_document),
    url(r'^delete/(?P<document_id>\d+)$', delete_document),
    url(r'^remove/(?P<document_id>\d+)$', remove_document),
    url(r'^(?P<document_id>\d+)/name$', update_name)
]
