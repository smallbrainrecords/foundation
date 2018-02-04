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
from django.conf.urls import patterns, include, url

urlpatterns = patterns('data_app.views',
                       url(r'^track/click$', 'track_observation_click'),
                       url(r'^(?P<observation_id>\d+)/info$', 'get_observation_info'),
                       url(r'^(?P<patient_id>\d+)/(?P<value_id>\d+)/individual_data_info$', 'get_individual_data_info'),
                       url(r'^(?P<patient_id>\d+)/get_datas$', 'get_datas'),
                       url(r'^(?P<patient_id>\d+)/add_new_data_type$', 'add_new_data_type'),
                       url(r'^(?P<patient_id>\d+)/(?P<observation_id>\d+)/save_data_type$', 'save_data_type'),
                       url(r'^(?P<patient_id>\d+)/(?P<observation_id>\d+)/delete_data$', 'delete_data'),
                       url(r'^updateOrder$', 'update_order'),
                       url(r'^(?P<observation_id>\d+)/get_pins$', 'get_pins'),
                       url(r'^(?P<patient_id>\d+)/pin_to_problem$', 'obseration_pin_to_problem'),
                       url(r'^(?P<patient_id>\d+)/(?P<component_id>\d+)/add_new_data$', 'add_new_data'),
                       url(r'^(?P<patient_id>\d+)/(?P<value_id>\d+)/delete_individual_data$', 'delete_individual_data'),
                       url(r'^(?P<patient_id>\d+)/(?P<value_id>\d+)/save_data$', 'save_data'),
                       url(r'^update_graph$', 'update_graph'),

                       # Allow to edit multiple observation component value
                       url(r'^(?P<patient_id>\d+)/delete$', 'delete_component_values'),
                       )
