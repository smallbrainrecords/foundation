(function(){

	'use strict';

	angular.module('ManagerApp').service('inrService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){
				var token = $cookies.csrftoken;
				return token;
			};

			this.getInrs = function(patient_id, problem_id) {
				var params = {};
				var url = '/inr/'+patient_id+ '/' + problem_id +'/get_inrs';
				return httpService.get(params, url);
			}
	});

})();