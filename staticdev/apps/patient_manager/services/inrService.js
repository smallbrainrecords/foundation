(function(){

	'use strict';

	angular.module('ManagerApp').service('inrService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){
				var token = $cookies.csrftoken;
				return token;
			};

			this.addMedication = function(form) {
				var url = '/inr/' + form.patient_id + '/' + form.inr_id + '/add_medication';
				return httpService.post(form, url);
			};

			this.addMedicationNote = function(form) {
				var url = '/inr/' + form.patient_id + '/' + form.medication_id + '/add_medication_note';
				return httpService.post(form, url);
			};

			this.editNote = function(form) {
				var url = '/inr/note/'+form.id+'/edit';
				return httpService.post(form, url);
			};

			this.deleteNote = function(form) {
				var url = '/inr/note/'+form.id+'/delete';
				return httpService.post(form, url);
			};

			this.fetchMedicationInfo = function (patient_id, medication_id) {
                var url = "/inr/" + patient_id + "/medication/" + medication_id + "/info";
                var params = {};
                return httpService.get(params, url);
            };

            this.fetchPinToProblem = function (medication_id) {
                var url = "/inr/medication/" + medication_id + "/get_pins";
                var params = {};

                return httpService.get(params, url);

            };

            this.medicationPinToProblem = function (patient_id, form) {
                var url = '/inr/medication/' + patient_id + '/pin_to_problem';
                return httpService.post(form, url);
            };

            this.listTerms = function(query){
				var params = {'query': query};
				var url = "/inr/list_terms";

				return httpService.get(params, url);
			};
	});

})();