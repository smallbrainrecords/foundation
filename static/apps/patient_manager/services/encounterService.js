(function(){

	'use strict';

	angular.module('ManagerApp').service('encounterService',
		function($http, $q, $cookies){


		this.csrf_token = function(){
			var token = $cookies.csrftoken;
			return token;
		};


		this.updateNote = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/enc/patient/'+form.patient_id+'/encounter/'+form.encounter_id+'/update_note',
				'data' : $.param(form),
				'headers':
				{
					'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
					'X-CSRFToken': this.csrf_token()
				}
			}).success(function(data){
				deferred.resolve(data);
			}).error(function(data){
				deferred.resolve(data);
			});

			return deferred.promise;

		};


		this.uploadAudio = function(form, file){

			var deferred = $q.defer();

			var uploadUrl = '/enc/patient/'+form.patient_id;
			uploadUrl += '/encounter/'+form.encounter_id;
			uploadUrl += '/upload_audio/';

			var fd = new FormData();

			angular.forEach(form, function(value, key){
				fd.append(key, value);
			})

			fd.append('file', file);

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


		this.uploadVideo = function(form, file){

			var deferred = $q.defer();
			
			var uploadUrl = '/enc/patient/'+form.patient_id;
			uploadUrl += '/encounter/'+form.encounter_id;
			uploadUrl += '/upload_video/';

			var fd = new FormData();

			angular.forEach(form, function(value, key){
				fd.append(key, value);
			})

			fd.append('file', file);

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




		});



})();