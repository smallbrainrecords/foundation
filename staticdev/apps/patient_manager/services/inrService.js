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
	});

})();