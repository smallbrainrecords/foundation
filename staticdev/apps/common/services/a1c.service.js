(function(){

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