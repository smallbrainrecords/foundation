(function(){

	'use strict';

	angular.module('AdminApp').service('adminService',
		function( $q, httpService){


		this.getUsersList = function(){
			var params = {};
			var url = '/project/admin/list/users/';
			return httpService.get(params, url);
		};


	});

})();