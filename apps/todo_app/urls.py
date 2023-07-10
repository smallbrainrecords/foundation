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
from todo_app.views import *

urlpatterns = [
    re_path(r"^patient/(?P<patient_id>\d+)/todos/add/new_todo$", add_patient_todo),
    re_path(r"^staff/(?P<user_id>\d+)/todos/add/new_todo$", add_staff_todo),
    re_path(r"^staff/(?P<user_id>\d+)/new_list$", add_staff_todo_list),
    re_path(r"^staff/all_todos/(?P<user_id>\d+)$", staff_all_todos),
    re_path(r"^todo/(?P<todo_id>\d+)/update/$", update_todo_status),
    re_path(r"^todo/updateOrder/$", update_order),
    re_path(r"^todo/(?P<todo_id>\d+)/info/$", get_todo_info),
    re_path(r"^todo/(?P<todo_id>\d+)/comment$", add_todo_comment),
    re_path(r"^todo/(?P<comment_id>\d+)/edit$", edit_todo_comment),
    re_path(r"^todo/(?P<comment_id>\d+)/delete$", delete_todo_comment),
    re_path(r"^todo/(?P<todo_id>\d+)/changeText$", change_todo_text),
    re_path(r"^todo/(?P<todo_id>\d+)/changeDueDate$", change_todo_due_date),
    re_path(r"^todo/(?P<label_id>\d+)/(?P<todo_id>\d+)/addLabel$", add_todo_label),
    re_path(
        r"^todo/removeLabel/(?P<label_id>\d+)/(?P<todo_id>\d+)$", remove_todo_label
    ),
    re_path(r"^todo/deleteLabel/(?P<label_id>\d+)$", delete_label),
    re_path(r"^todo/newLabel/(?P<todo_id>\d+)$", new_todo_label),
    re_path(r"^todo/accessEncounter/(?P<todo_id>\d+)$", todo_access_encounter),
    re_path(r"^todo/(?P<todo_id>\d+)/addAttachment$", add_todo_attachment),
    re_path(r"^todo/(?P<todo_id>\d+)/(?P<last_id>\d+)/activity/$", get_todo_activity),
    re_path(r"^todo/(?P<todo_id>\d+)/addMember$", add_todo_member),
    re_path(r"^todo/(?P<todo_id>\d+)/removeMember$", remove_todo_member),
    re_path(r"^todo/(?P<user_id>\d+)/getlabels$", get_labels),
    re_path(r"^todo/(?P<user_id>\d+)/getLabeledTodoList$", get_user_label_lists),
    re_path(r"^todo/saveEditLabel/(?P<label_id>\d+)$", save_edit_label),
    re_path(r"^todo/user_todos/(?P<user_id>\d+)$", get_user_todos),
    re_path(r"^todo/(?P<list_id>\d+)/deleteTodoList$", delete_todo_list),
    re_path(r"^todo/(?P<list_id>\d+)/open_todo_list$", open_todo_list),
    re_path(
        r"^attachment/(?P<attachment_id>\d+)/downloadAttachment$", download_attachment
    ),
    re_path(r"^attachment/(?P<attachment_id>\d+)/delete$", delete_attachment),
    re_path(r"^activities$", batch_save_activities),
]
