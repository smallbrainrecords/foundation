(function () {

    'use strict';

    angular.module('ManagerApp').service('medicationService',
        function ($http, $q, $cookies, httpService) {
            return {
                csrf_token: csrf_token,
                addMedication: addMedication,
                addMedicationNote: addMedicationNote,
                editNote: editNote,
                deleteNote: deleteNote,
                fetchMedicationInfo: fetchMedicationInfo,
                fetchPinToProblem: fetchPinToProblem,
                medicationPinToProblem: medicationPinToProblem,
                listTerms: listTerms,
                changeActiveMedication: changeActiveMedication,
                changeDosage: changeDosage,
            };

            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            function addMedication(form) {
                let url = `/medication/${form.patient_id}/add_medication`;
                return httpService.post(form, url);
            }

            function addMedicationNote(form) {
                let url = `/medication/${form.patient_id}/${form.medication_id}/add_medication_note`;
                return httpService.post(form, url);
            }

            function editNote(form) {
                let url = `/medication/note/${form.id}/edit`;
                return httpService.post(form, url);
            }

            function deleteNote(form) {
                let url = `/medication/note/${form.id}/delete`;
                return httpService.post(form, url);
            }

            function fetchMedicationInfo(patient_id, medication_id) {
                let url = `/medication/${patient_id}/medication/${medication_id}/info`;
                let params = {};
                return httpService.get(params, url);
            }

            function fetchPinToProblem(medication_id) {
                let url = `/medication/${medication_id}/get_pins`;
                let params = {};

                return httpService.get(params, url);

            }

            function medicationPinToProblem(patient_id, form) {
                let url = `/medication/${patient_id}/pin_to_problem`;
                return httpService.post(form, url);
            }

            function listTerms(query) {
                let params = {'query': query};
                let url = '/medication/list_terms';

                return httpService.get(params, url);
            }

            function changeActiveMedication(patient_id, medication_id) {
                let url = `/medication/${patient_id}/${medication_id}/change_active_medication`;
                return httpService.post({}, url);
            }
            /**
             * Change medication dosage
             * @returns {HttpPromise}
             * @param patientId
             * @param medicationId
             * @param medicationObj
             */
            function changeDosage(patientId, medicationId, medicationObj) {
                let url = `/medication/${patientId}/${medicationId}/change_dosage`;
                return $http.post(url,medicationObj, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            }
        });

})();