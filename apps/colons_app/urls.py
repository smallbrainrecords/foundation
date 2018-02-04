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

urlpatterns = patterns('colons_app.views',
                       url(r'^(?P<colon_id>\d+)/info$', 'get_colon_info'),
                       url(r'^study/(?P<study_id>\d+)/info$', 'get_study_info'),
                       url(r'^(?P<colon_id>\d+)/add_study$', 'add_study'),
                       url(r'^(?P<study_id>\d+)/delete_study$', 'delete_study'),
                       url(r'^(?P<study_id>\d+)/edit_study$', 'edit_study'),
                       url(r'^study/(?P<study_id>\d+)/upload_image$', 'upload_study_image'),
                       url(r'^study/(?P<study_id>\d+)/image/(?P<image_id>\d+)/delete/$', 'delete_study_image'),
                       url(r'^study/(?P<study_id>\d+)/addImage$', 'add_study_image'),
                       url(r'^(?P<colon_id>\d+)/add_factor$', 'add_factor'),
                       url(r'^(?P<colon_id>\d+)/delete_factor$', 'delete_factor'),
                       url(r'^(?P<colon_id>\d+)/refuse$', 'refuse'),
                       url(r'^(?P<colon_id>\d+)/not_appropriate$', 'not_appropriate'),
                       url(r'^(?P<colon_id>\d+)/track/click$', 'track_colon_click'),
                       url(r'^(?P<colon_id>\d+)/add_note$', 'add_note'),
                       url(r'^note/(?P<note_id>\d+)/edit$', 'edit_note'),
                       url(r'^note/(?P<note_id>\d+)/delete$', 'delete_note'),
                       )
