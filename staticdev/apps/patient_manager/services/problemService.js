(function(){

	'use strict';

	angular.module('ManagerApp').service('problemService',
		function($http, $q, $cookies){


		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};


		this.updateProblemStatus = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/patient/'+form.patient_id+'/problem/'+form.problem_id+'/update_status',
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



		this.trackProblemClickEvent = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/problem/'+form.problem_id+'/track/click/',
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



		this.updateStartDate = function(form){

			

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/patient/'+form.patient_id+'/problem/'+form.problem_id+'/update_start_date',
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


		this.addPatientNote = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/patient/'+form.patient_id+'/problem/'+form.problem_id+'/add_patient_note',
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

		this.addPhysicianNote = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/patient/'+form.patient_id+'/problem/'+form.problem_id+'/add_physician_note',
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

		this.addGoal = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/patient/'+form.patient_id+'/problem/'+form.problem_id+'/add_goal',
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


		this.addTodo = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/patient/'+form.patient_id+'/problem/'+form.problem_id+'/add_todo',
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

		this.deleteProblemImage = function(form){

			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/problem/'+form.problem_id+'/image/'+form.image_id+'/delete/',
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


		this.relateProblem = function(form){



			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : '/p/problem/relate/',
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