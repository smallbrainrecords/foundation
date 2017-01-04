(function () {

    'use strict';

    angular.module('ManagerApp').service('medicationService',
        function ($http, $q, $cookies, httpService) {

            this.csrf_token = function () {
                var token = $cookies.get('csrftoken');
                return token;
            };

            this.addMedication = function (form) {
                var url = '/medication/' + form.patient_id + '/add_medication';
                return httpService.post(form, url);
            };

            this.addMedicationNote = function (form) {
                var url = '/medication/' + form.patient_id + '/' + form.medication_id + '/add_medication_note';
                return httpService.post(form, url);
            };

            this.editNote = function (form) {
                var url = '/medication/note/' + form.id + '/edit';
                return httpService.post(form, url);
            };

            this.deleteNote = function (form) {
                var url = '/medication/note/' + form.id + '/delete';
                return httpService.post(form, url);
            };

            this.fetchMedicationInfo = function (patient_id, medication_id) {
                var url = "/medication/" + patient_id + "/medication/" + medication_id + "/info";
                var params = {};
                return httpService.get(params, url);
            };

            this.fetchPinToProblem = function (medication_id) {
                var url = "/medication/" + medication_id + "/get_pins";
                var params = {};

                return httpService.get(params, url);

            };

            this.medicationPinToProblem = function (patient_id, form) {
                var url = '/medication/' + patient_id + '/pin_to_problem';
                return httpService.post(form, url);
            };

            this.listTerms = function (query) {
                var params = {'query': query};
                var url = "/medication/list_terms";

                return httpService.get(params, url);
            };

            this.changeActiveMedication = function (patient_id, medication_id) {
                var url = '/medication/' + patient_id + '/' + medication_id + '/change_active_medication';
                return httpService.post({}, url);
            };

            /**
             * Change medication dosage
             * @param patient_id
             * @param medication
             * @returns {HttpPromise}
             */
            this.changeDosage = function (patientId, medicationId, medicationObj) {
                var url = '/medication/' + patientId + '/' + medicationId + '/change_dosage';
                return $http.post(url,medicationObj, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            };
        });

})();