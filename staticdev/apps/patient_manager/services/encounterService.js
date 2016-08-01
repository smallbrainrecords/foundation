(function(){

	'use strict';

	angular.module('ManagerApp').service('encounterService',
		function($http, $q, $cookies, httpService){


		this.updateNote = function(form){

			var url  = '/enc/patient/'+form.patient_id+'/encounter/'+form.encounter_id+'/update_note';
			return httpService.post(form, url);

		};

		this.addTimestamp = function(form){

			var url  = '/enc/patient/'+form.patient_id+'/encounter/'+form.encounter_id+'/add_timestamp';
			return httpService.post(form, url);

		};

		this.markFavoriteEvent = function(form){
			var url  = '/enc/encounter_event/'+form.encounter_event_id+'/mark_favorite';
			return httpService.post(form, url);
		};

		this.nameFavoriteEvent = function(form){
			var url  = '/enc/encounter_event/'+form.encounter_event_id+'/name_favorite';
			return httpService.post(form, url);
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

            		headers: {'Content-Type': undefined,'X-CSRFToken': this.csrf_token()}
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

            		headers: {'Content-Type': undefined,'X-CSRFToken': this.csrf_token()}
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