(function(){

	'use strict';

	angular.module('ManagerApp').service('observationService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){

				var token = $cookies.csrftoken;
				return token;
			};

			this.fetchObservationInfo = function(observation_id){
				var url = "/observation/"+observation_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

			this.addNote = function(form) {
				var url = '/observation/'+form.observation_id+'/add_note';
				return httpService.post(form, url);
			};

			this.editNote = function(form) {
				var url = '/observation/note/'+form.id+'/edit';

				return httpService.post(form, url);
			};

			this.deleteNote  = function(form) {
				var url = '/observation/note/'+form.id+'/delete';

				return httpService.post(form, url);
			};

			this.addNewValue = function(form) {
				var url = '/observation/'+form.observation_id+'/add_value';
				return httpService.post(form, url);
			}
	});

})();