/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
(function () {

    'use strict';

    angular.module('app.services')
        .service('a1cService', function ($http, $q, $cookies, httpService) {

            return {
                csrf_token: csrf_token,
                fetchA1cInfo: fetchA1cInfo,
                fetchObservationComponentInfo: fetchObservationComponentInfo,
                fetchObservationValueInfo: fetchObservationValueInfo,
                addNote: addNote,
                editNote: editNote,
                deleteNote: deleteNote,
                addNewValue: addNewValue,
                deleteValue: deleteValue,
                editValue: editValue,
                addValueNote: addValueNote,
                editValueNote: editValueNote,
                deleteValueNote: deleteValueNote,
                addValueRefused: addValueRefused,
                trackA1cClickEvent: trackA1cClickEvent,
            };

            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            function fetchA1cInfo(a1c_id) {
                let url = `/a1c/${a1c_id}/info`;
                let params = {};

                return httpService.get(params, url);

            }

            function fetchObservationComponentInfo(component_id) {
                let url = `/a1c/${component_id}/component_info`;
                let params = {};

                return httpService.get(params, url);

            }

            function fetchObservationValueInfo(value_id) {
                let url = `/a1c/${value_id}/value_info`;
                let params = {};

                return httpService.get(params, url);

            }

            function addNote(form) {
                let url = `/a1c/${form.a1c_id}/add_note`;
                return httpService.post(form, url);
            }

            function editNote(form) {
                let url = `/a1c/note/${form.id}/edit`;

                return httpService.post(form, url);
            }

            function deleteNote(form) {
                let url = `/a1c/note/${form.id}/delete`;

                return httpService.post(form, url);
            }

            function addNewValue(form) {
                let url = `/a1c/${form.component_id}/add_value`;
                return httpService.post(form, url);
            }

            function deleteValue(value) {
                let url = `/a1c/value/${value.id}/delete`;

                return httpService.post(value, url);
            }

            function editValue(form) {
                let url = `/a1c/value/${form.value_id}/edit`;

                return httpService.post(form, url);
            }

            function addValueNote(form) {
                let url = `/a1c/value/${form.value_id}/add_note`;
                return httpService.post(form, url);
            }

            function editValueNote(form) {
                let url = `/a1c/value/note/${form.id}/edit`;

                return httpService.post(form, url);
            }

            function deleteValueNote(form) {
                let url = `/a1c/value/note/${form.id}/delete`;

                return httpService.post(form, url);
            }

            function addValueRefused(form) {
                let url = `/a1c/${form.a1c_id}/patient_refused`;
                return httpService.post(form, url);
            }

            function trackA1cClickEvent(form) {
                let url = `/a1c/${form.a1c_id}/track/click/`;
                return httpService.post(form, url);
            }
        });

})();