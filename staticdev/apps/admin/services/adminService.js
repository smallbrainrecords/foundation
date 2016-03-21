(function(){

	'use strict';

	angular.module('AdminApp').service('adminService',
		function( $q,$cookies, $http, httpService){

		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};



		this.fetchActiveUser = function(){

			var params = {};
			var url = '/u/active/user/';

			return httpService.get(params, url);

		};

		this.getUsersList = function(form){
			var params = form;
			var url = '/project/admin/list/registered/users/';
			return httpService.get(params, url);
		};


		this.getPendingRegistrationUsersList = function(form){
			var params = form;
			var url = '/project/admin/list/unregistered/users/';
			return httpService.get(params, url);
		};


		this.getUserInfo = function(user_id){

			var params = {user_id:user_id};
			var url = '/project/admin/user/'+user_id+'/info/';
			return httpService.get(params, url);

		};

		this.approveUser = function(user){

			var form = user;
			var url = '/project/admin/user/approve/';
			return httpService.post(form, url);

		};

		this.updateBasicProfile = function(form){
			var url = '/project/admin/user/update/basic/';
			return httpService.post(form, url);

		};


		this.updateProfile = function(form, files ){
        

        	var deferred = $q.defer();

        	var uploadUrl = '/project/admin/user/update/profile/';

        	var fd = new FormData();

        	fd.append('csrfmiddlewaretoken', this.csrf_token() );

        	angular.forEach(form, function(value, key) {
  					fd.append(key, value);
			});

        	angular.forEach(files, function(value, key){
        		fd.append(key, value);
        	});
        	

        	$http.post(uploadUrl, fd, {
            		transformRequest: angular.identity,

            		headers: {'Content-Type': undefined}
    	    	})
	        	.success(function(data){
	        		deferred.resolve(data);
        		})
        		.error(function(data){
        			deferred.resolve(data);

        		});

        	return deferred.promise;

    	};



		this.updateEmail = function(form){
			var url = '/project/admin/user/update/email/';
			return httpService.post(form, url);
		};

		this.updatePassword = function(form){
			var url = '/project/admin/user/update/password/';
			return httpService.post(form, url);
		};

		this.addUser = function(form){
			var url  = '/project/admin/user/create/';
			return httpService.post(form, url);
		};


		this.getPatientPhysicians = function(params){

			var url = '/project/admin/patient/physicians/';
			return httpService.get(params, url);

		};

		this.getPhysicianData= function(params){

			var url = '/project/admin/physician/data/';
			return httpService.get(params, url);
		};

		this.getAssignedPhysicians = function(params){
			var url = '/project/admin/assigned/physicians/';
			return httpService.get(params, url);
		};

		this.assignMember = function(form){

			var url = '/project/admin/physician/assign/member/';
			return httpService.post(form, url);
		};

		this.unassignMember = function(form){
			var url = '/project/admin/physician/unassign/member/';
			return httpService.post(form, url);
		};

	});

})();