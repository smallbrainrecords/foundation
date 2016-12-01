(function(){

	'use strict';

	angular.module('AdminApp').service('adminService',
		function( $q,$cookies, $http, httpService){

		this.csrf_token = function(){

			var token = $cookies.get('csrftoken');
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

		this.getPatientsList = function(){
			var form = {};
			var url = '/u/patients/';
			return httpService.post(form, url);
		};

		this.getSharingPatients = function(patient_id){
			var form = {};
			var url = '/u/sharing_patients/' + patient_id;
			return httpService.post(form, url);
		};

		this.addSharingPatient = function(form){
			var url = '/u/patient/add_sharing_patient/' + form.patient_id + '/' + form.sharing_patient_id;
			return httpService.post(form, url);
		};

		this.removeSharingPatient = function(patient_id, sharing_patient_id){
			var form = {};
			var url = '/u/patient/remove_sharing_patient/' + patient_id + '/' + sharing_patient_id;
			return httpService.post(form, url);
		};

		this.fetchProblems = function(patient_id){
			var params = {};
			var url ='/p/problem/' + patient_id + '/getproblems';
			return httpService.get(params, url);
		};

		this.fetchSharingProblems = function(patient_id, sharing_patient_id){
			var params = {};
			var url ='/p/problem/' + patient_id + '/' + sharing_patient_id + '/get_sharing_problems';
			return httpService.get(params, url);
		};

		this.removeSharingProblems = function(patient_id, sharing_patient_id, problem_id){
			var params = {};
			var url ='/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/remove_sharing_problems';
			return httpService.post(params, url);
		};

		this.addSharingProblems = function(patient_id, sharing_patient_id, problem_id){
			var params = {};
			var url ='/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/add_sharing_problems';
			return httpService.post(params, url);
		};

		this.updateActive = function(form){
			var url = '/project/admin/user/update/active/';
			return httpService.post(form, url);
		};

		this.updateDeceasedDate = function(form){
			var url = '/project/admin/user/update/deceased_date/';
			return httpService.post(form, url);
		};

	});

})();