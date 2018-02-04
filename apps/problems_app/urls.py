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
from django.conf.urls import patterns, url

urlpatterns = patterns('problems_app.views', url(r'^problem/(?P<problem_id>\d+)/info$', 'get_problem_info'),
                       url(r'^problem/(?P<problem_id>\d+)/(?P<last_id>\d+)/activity/$', 'get_problem_activity'),
                       url(r'^problem/(?P<problem_id>\d+)/track/click/$', 'track_problem_click'),
                       url(r'^patient/(?P<patient_id>\d+)/problems/add/new_problem$', 'add_patient_problem'),
                       url(r'^patient/(?P<patient_id>\d+)/problems/add/new_common_problem$',
                           'add_patient_common_problem'),
                       url(r'^problem/(?P<problem_id>\d+)/delete$', 'delete_problem'),
                       url(r'^problem/(?P<problem_id>\d+)/change_name$', 'change_name'),
                       url(r'^problem/(?P<problem_id>\d+)/update_status$', 'update_problem_status'),
                       url(r'^problem/(?P<problem_id>\d+)/update_start_date$', 'update_start_date'),
                       url(r'^problem/(?P<problem_id>\d+)/add_wiki_note$', 'add_wiki_note'),
                       url(r'^problem/(?P<problem_id>\d+)/add_history_note$', 'add_history_note'),
                       url(r'^problem/(?P<problem_id>\d+)/add_goal$', 'add_problem_goal'),
                       url(r'^problem/(?P<problem_id>\d+)/add_todo$', 'add_problem_todo'),
                       url(r'^problem/(?P<problem_id>\d+)/upload_image$', 'upload_problem_image'),
                       url(r'^problem/(?P<problem_id>\d+)/image/(?P<image_id>\d+)/delete/$', 'delete_problem_image'),
                       url(r'^problem/(?P<problem_id>\d+)/a1c$', 'get_a1c'),
                       url(r'^problem/(?P<problem_id>\d+)/colon_cancers$', 'get_colon_cancers'),
                       url(r'^problem/relate/$', 'relate_problem'),
                       url(r'^problem/updateOrder/$', 'update_order'),
                       url(r'^problem/update_by_ptw/$', 'update_by_ptw'),
                       url(r'^problem/update_state_to_ptw/$', 'update_state_to_ptw'),
                       url(r'^problem/newLabel/(?P<problem_id>\d+)$', 'new_problem_label'),
                       url(r'^problem/(?P<patient_id>\d+)/(?P<user_id>\d+)/getlabels$', 'get_problem_labels'),
                       url(r'^problem/saveEditLabel/(?P<label_id>\d+)/(?P<patient_id>\d+)/(?P<user_id>\d+)$',
                           'save_edit_problem_label'),
                       url(r'^problem/(?P<label_id>\d+)/(?P<problem_id>\d+)/addLabel$', 'add_problem_label'),
                       url(r'^problem/removeLabel/(?P<label_id>\d+)/(?P<problem_id>\d+)$', 'remove_problem_label'),
                       url(r'^problem/deleteLabel/(?P<label_id>\d+)$', 'delete_problem_label'),
                       url(r'^problem/(?P<patient_id>\d+)/(?P<user_id>\d+)/new_list$', 'add_problem_list'),
                       url(r'^problem/(?P<list_id>\d+)/deleteProblemList$', 'delete_problem_list'),
                       url(r'^problem/(?P<list_id>\d+)/renameProblemList$', 'rename_problem_list'),
                       url(r'^problem/(?P<list_id>\d+)/update_problem_list_note$', 'update_problem_list_note'),
                       url(r'^problem/(?P<patient_id>\d+)/(?P<user_id>\d+)/getLabeledProblemLists$',
                           'get_label_problem_lists'),
                       url(r'^problem/(?P<patient_id>\d+)/getproblems$', 'get_problems'),
                       url(r'^problem/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)/get_sharing_problems$',
                           'get_sharing_problems'),
                       url(
                           r'^problem/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)/(?P<problem_id>\d+)/remove_sharing_problems$',
                           'remove_sharing_problems'),
                       url(
                           r'^problem/(?P<patient_id>\d+)/(?P<sharing_patient_id>\d+)/(?P<problem_id>\d+)/add_sharing_problems$',
                           'add_sharing_problems'),
                       url(r'^problem/staff/(?P<staff_id>\d+)/add_new_common_problem$', 'add_new_common_problem'),
                       url(r'^problem/staff/(?P<staff_id>\d+)/get_common_problems$', 'get_common_problems'),
                       url(r'^problem/remove_common_problem/(?P<problem_id>\d+)$', 'remove_common_problem'),
                       url(r'^problem/(?P<problem_id>\d+)/get_data_pins$', 'get_data_pins'),
                       url(r'^problem/(?P<problem_id>\d+)/get_medication_pins$', 'get_medication_pins'),

                       # API used for optimize problem loading page AND more semantics URLs/RESTFUL
                       url(r'^problem/(?P<problem_id>\d+)/todos$', 'get_problem_todos'),
                       url(r'^problem/(?P<problem_id>\d+)/wikis$', 'get_problem_wikis'),
                       url(r'^problem/(?P<problem_id>\d+)/goals$', 'get_problem_goals'),
                       url(r'^problem/(?P<problem_id>\d+)/images$', 'get_problem_images'),
                       url(r'^problem/(?P<problem_id>\d+)/relationships', 'get_problem_relationships'),
                       url(r'^problem/(?P<problem_id>\d+)/encounters$', 'get_related_encounters'),
                       url(r'^problem/(?P<problem_id>\d+)/documents$', 'get_related_documents'),
                       )
