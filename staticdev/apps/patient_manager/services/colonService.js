(function(){

	'use strict';

	angular.module('ManagerApp').service('colonService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){

				var token = $cookies.csrftoken;
				return token;
			};

			this.fetchColonCancerInfo = function(colon_id){
				var url = "/colon_cancer/"+colon_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

			this.fetchColonCancerStudyInfo = function(study_id){
				var url = "/colon_cancer/study/"+study_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

			this.addNewStudy = function(colon_id, study) {
				var url = '/colon_cancer/'+colon_id+'/add_study';
				return httpService.post(study, url);
			};

			this.deleteStudy = function(study) {
				var url = '/colon_cancer/'+study.id+'/delete_study';
				return httpService.post(study, url);
			};

			this.saveStudy = function(study) {
				var url = '/colon_cancer/'+study.id+'/edit_study';
				return httpService.post(study, url);
			};
	});

})();