(function(){

	'use strict';


	angular.module('ManagerApp').service('patientService',
		function($http, $q, $cookies){


		this.fetchPatientInfo = function(patient_id){

			var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/patient/"+patient_id+"/info",
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;
		};


		this.fetchProblemInfo = function(problem_id){

			var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/problem/"+problem_id+"/info",
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;
		};




		});


})();