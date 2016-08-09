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

			this.deleteStudyImage = function(form){

				var url = '/colon_cancer/study/'+form.study_id+'/image/'+form.image_id+'/delete/';
				return httpService.post(form, url);
			};

			this.addImage = function(form, file){
	        	var deferred = $q.defer();

	        	var uploadUrl = '/colon_cancer/study/'+form.study_id+'/addImage';

	        	var fd = new FormData();

	        	fd.append(0, file);

	        	$http.post(uploadUrl, fd, {
	            		transformRequest: angular.identity,
	            		headers: {'Content-Type': undefined, 'X-CSRFToken': this.csrf_token()}
	    	    	})
		        	.success(function(data){
		        		deferred.resolve(data);
	        		})
	        		.error(function(data){
	        			deferred.resolve(data);

	        		});

	        	return deferred.promise;
	    	};

	    	this.addFactor = function(colon_id, factor) {
				var url = '/colon_cancer/'+colon_id+'/add_factor';
				return httpService.post(factor, url);
			};

			this.deleteFactor  = function(colon_id, factor) {
				var url = '/colon_cancer/'+colon_id+'/delete_factor';
				return httpService.post(factor, url);
			};
	});

})();