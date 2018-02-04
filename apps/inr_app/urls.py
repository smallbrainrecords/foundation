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

urlpatterns = patterns('inr_app.views',
                       url(r'^(?P<patient_id>\d+)/target/get$', 'get_inr_target'),
                       url(r'^(?P<patient_id>\d+)/target/set$', 'set_inr_target'),
                       url(r'^(?P<patient_id>\d+)/inrs', 'get_inr_table'),
                       url(r'^(?P<patient_id>\d+)/inr/add', 'add_inr'),
                       url(r'^(?P<patient_id>\d+)/inr/update', 'update_inr'),
                       url(r'^(?P<patient_id>\d+)/inr/delete', 'delete_inr'),
                       url(r'^(?P<patient_id>\d+)/problems', 'get_problems'),
                       url(r'^(?P<patient_id>\d+)/medications', 'get_medications'),
                       url(r'^(?P<patient_id>\d+)/(?P<problem_id>\d+)/orders', 'get_orders'),
                       url(r'^(?P<patient_id>\d+)/order/add', 'add_order'),
                       url(r'^(?P<patient_id>\d+)/notes', 'get_inr_note'),
                       url(r'^(?P<patient_id>\d+)/note/add', 'add_note'),
                       url(r'^patients', 'find_patient')
                       )
