(function(){

	'use strict';

	angular.module('AdminApp').service('adminService',
		function( $q, httpService){


		this.getUsersList = function(){
			var params = {};
			var url = '/project/admin/list/users/';
			return httpService.get(params, url);
		};



		this.getUserInfo = function(user_id){

			var params = {user_id:user_id};
			var url = '/project/admin/user/'+user_id+'/info/';
			return httpService.get(params, url);

		};

	});

})();