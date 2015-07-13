(function(){

	'use strict';

	angular.module('ManagerApp').service('goalService',
		function($http, $q, $cookies){


		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};


		this.updateGoalStatus = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/g/patient/'+form.patient_id+'/goal/'+form.goal_id+'/update_status',
				'data' : $.param(form),
				'headers':
				{
					'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
				}
			}).success(function(data){
				deferred.resolve(data);
			}).error(function(data){
				deferred.resolve(data);
			});

			return deferred.promise;

		};


		this.addNote = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/g/patient/'+form.patient_id+'/goal/'+form.goal_id+'/add_note',
				'data' : $.param(form),
				'headers':
				{
					'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
				}
			}).success(function(data){
				deferred.resolve(data);
			}).error(function(data){
				deferred.resolve(data);
			});

			return deferred.promise;

		};


		});



})();