(function(){

	'use strict';

	angular.module('StaffApp').service('physicianService',
		function( $q,$cookies, $http, httpService){

		this.csrf_token = function(){
			var token = $cookies.get('csrftoken');
			return token;
		};

		this.getUsersList = function(form){
			var params = form;
			var url = '/project/admin/list/registered/users/';
			return httpService.get(params, url);
		};

		this.getPhysicianData= function(params){

			var url = '/project/admin/physician/data/';
			return httpService.get(params, url);
		};

	});

})();