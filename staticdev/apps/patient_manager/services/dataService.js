(function(){

	'use strict';

	angular.module('ManagerApp').service('dataService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){

				var token = $cookies.csrftoken;
				return token;
			};

			this.fetchDataInfo = function(data_id){
				var url = "/data/"+data_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

			this.fetchPinToProblem = function(data_id){
				var url = "/data/"+data_id+"/get_pins";
				var params = {};

				return httpService.get(params, url);

			};

			this.dataPinToProblem = function(patient_id, form) {
				var url = '/data/'+patient_id+'/pin_to_problem';
				return httpService.post(form, url);
			};

			this.addData = function(patient_id, data_id, form) {
				var url = '/data/'+patient_id + '/' + data_id + '/add_new_data';
				return httpService.post(form, url);
			};

			this.fetchIndividualDataInfo = function(patient_id, component_id){
				var url = "/data/"+ patient_id + "/" +component_id+"/individual_data_info";
				var params = {};

				return httpService.get(params, url);

			};

			this.deleteIndividualData = function(patient_id, component_id) {
				var form = {};
				var url = "/data/"+ patient_id + "/" +component_id+"/delete_individual_data";
				return httpService.post(form, url);
			};

			this.saveData = function(patient_id, component_id, form) {
				var url = '/data/'+patient_id + '/' + component_id + '/save_data';
				return httpService.post(form, url);
			};

	});

})();