(function(){

	'use strict';

	angular.module('StaffApp').service('staffService',
		function( $q,$cookies, $http, httpService){

		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};

		this.getPatientsList = function(){
			var form = {};
			var url = '/u/patients/';
			return httpService.post(form, url);
		};

	});

})();