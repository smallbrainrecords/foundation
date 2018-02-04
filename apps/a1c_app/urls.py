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


urlpatterns = patterns('a1c_app.views',

    url(r'^(?P<a1c_id>\d+)/info$', 'get_a1c_info'),
    url(r'^(?P<value_id>\d+)/value_info$', 'get_observation_value_info'),
    url(r'^(?P<a1c_id>\d+)/add_note$', 'add_note'),
    url(r'^(?P<component_id>\d+)/add_value$', 'add_value'),
    url(r'^(?P<a1c_id>\d+)/patient_refused$', 'patient_refused'),
    url(r'^note/(?P<note_id>\d+)/edit$', 'edit_note'),
    url(r'^note/(?P<note_id>\d+)/delete$', 'delete_note'),
    url(r'^value/(?P<value_id>\d+)/delete$', 'delete_value'),
    url(r'^value/(?P<value_id>\d+)/edit$', 'edit_value'),
    url(r'^value/(?P<value_id>\d+)/add_note$', 'add_value_note'),
    url(r'^value/note/(?P<note_id>\d+)/edit$', 'edit_value_note'),
    url(r'^value/note/(?P<note_id>\d+)/delete$', 'delete_value_note'),
    url(r'^(?P<a1c_id>\d+)/track/click/$',
        'track_a1c_click'),
)
