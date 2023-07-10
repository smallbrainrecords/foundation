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
from problems_app.views import *

urlpatterns = [
    re_path(r"^problem/(?P<problem_id>\d+)/info$", get_problem_info),
    re_path(
        r"^problem/(?P<problem_id>\d+)/(?P<last_id>\d+)/activity/$",
        get_problem_activity,
    ),
    re_path(r"^problem/(?P<problem_id>\d+)/track/click/$", track_problem_click),
    re_path(
        r"^patient/(?P<patient_id>\d+)/problems/add/new_problem$", add_patient_problem
    ),
    re_path(
        r"^patient/(?P<patient_id>\d+)/problems/add/new_common_problem$",
        add_patient_common_problem,
    ),
    re_path(r"^problem/(?P<problem_id>\d+)/delete$", delete_problem),
    re_path(r"^problem/(?P<problem_id>\d+)/change_name$", change_name),
    re_path(r"^problem/(?P<problem_id>\d+)/update_status$", update_problem_status),
    re_path(r"^problem/(?P<problem_id>\d+)/update_start_date$", update_start_date),
    re_path(r"^problem/(?P<problem_id>\d+)/add_wiki_note$", add_wiki_note),
    re_path(r"^problem/(?P<problem_id>\d+)/add_history_note$", add_history_note),
    re_path(r"^problem/(?P<problem_id>\d+)/add_goal$", add_problem_goal),
    re_path(r"^problem/(?P<problem_id>\d+)/add_todo$", add_problem_todo),
    re_path(r"^problem/(?P<problem_id>\d+)/upload_image$", upload_problem_image),
    re_path(
        r"^problem/(?P<problem_id>\d+)/image/(?P<image_id>\d+)/delete/$",
        delete_problem_image,
    ),
    re_path(r"^problem/(?P<problem_id>\d+)/a1c$", get_a1c),
    re_path(r"^problem/(?P<problem_id>\d+)/colon_cancers$", get_colon_cancers),
    re_path(r"^problem/relate/$", relate_problem),
    re_path(r"^problem/updateOrder/$", update_order),
    re_path(r"^problem/update_by_ptw/$", update_by_ptw),
    re_path(r"^problem/update_state_to_ptw/$", update_state_to_ptw),
    re_path(r"^problem/newLabel/(?P<problem_id>\d+)$", new_problem_label),
    re_path(
        r"^problem/(?P<patient_id>\d+)/(?P<user_id>\d+)/getlabels$", get_problem_labels
    ),
    re_path(
        r"^problem/saveEditLabel/(?P<label_id>\d+)/(?P<patient_id>\d+)/(?P<user_id>\d+)$",
        save_edit_problem_label,
    ),
    re_path(
        r"^problem/(?P<label_id>\d+)/(?P<problem_id>\d+)/addLabel$", add_problem_label
    ),
    re_path(
        r"^problem/removeLabel/(?P<label_id>\d+)/(?P<problem_id>\d+)$",
        remove_problem_label,
    ),
    re_path(r"^problem/deleteLabel/(?P<label_id>\d+)$", delete_problem_label),
    re_path(
        r"^problem/(?P<patient_id>\d+)/(?P<user_id>\d+)/new_list$", add_problem_list
    ),
    re_path(r"^problem/(?P<list_id>\d+)/deleteProblemList$", delete_problem_list),
    re_path(r"^problem/(?P<list_id>\d+)/renameProblemList$", rename_problem_list),
    re_path(
        r"^problem/(?P<list_id>\d+)/update_problem_list_note$", update_problem_list_note
    ),
    re_path(
        r"^problem/(?P<patient_id>\d+)/(?P<user_id>\d+)/getLabeledProblemLists$",
        get_label_problem_lists,
    ),
    re_path(r"^problem/(?P<patient_id>\d+)/getproblems$", get_problems),
    re_path(
        r"^problem/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)/get_sharing_problems$",
        get_sharing_problems,
    ),
    re_path(
        r"^problem/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)/(?P<problem_id>\d+)/remove_sharing_problems$",
        remove_sharing_problems,
    ),
    re_path(
        r"^problem/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)/(?P<problem_id>\d+)/add_sharing_problems$",
        add_sharing_problems,
    ),
    re_path(
        r"^problem/staff/(?P<staff_id>\d+)/add_new_common_problem$",
        add_new_common_problem,
    ),
    re_path(
        r"^problem/staff/(?P<staff_id>\d+)/get_common_problems$", get_common_problems
    ),
    re_path(
        r"^problem/remove_common_problem/(?P<problem_id>\d+)$", remove_common_problem
    ),
    re_path(r"^problem/(?P<problem_id>\d+)/get_data_pins$", get_data_pins),
    re_path(r"^problem/(?P<problem_id>\d+)/get_medication_pins$", get_medication_pins),
    # API used for optimize problem loading page AND more semantics URLs/RESTFUL
    re_path(r"^problem/(?P<problem_id>\d+)/todos$", get_problem_todos),
    re_path(r"^problem/(?P<problem_id>\d+)/wikis$", get_problem_wikis),
    re_path(r"^problem/(?P<problem_id>\d+)/goals$", get_problem_goals),
    re_path(r"^problem/(?P<problem_id>\d+)/images$", get_problem_images),
    re_path(r"^problem/(?P<problem_id>\d+)/relationships", get_problem_relationships),
    re_path(r"^problem/(?P<problem_id>\d+)/encounters$", get_related_encounters),
    re_path(r"^problem/(?P<problem_id>\d+)/documents$", get_related_documents),
    re_path(r"^problem/(?P<problem_id>\d+)/notes$", problem_notes_function),
]
