(function(){

	'use strict';


	angular.module('ManagerApp').service('patientService',
		function($http, $q, $cookies){



		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};

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


		this.fetchGoalInfo = function(goal_id){
			var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/goal/"+goal_id+"/info",
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;
		};


		this.fetchEncounterInfo = function(encounter_id){
			var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/encounter/"+encounter_id+"/info",
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;
		};



		this.getEncounterStatus = function(patient_id){

			var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/patient/"+patient_id+"/encounter/status",
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;

		};

		this.startNewEncounter = function(patient_id){

		var deferred = $q.defer();


		var data = {
			'patient_id':patient_id,
			'csrfmiddlewaretoken':this.csrf_token()
		}

		$http({

			'method':'POST',
			'url' : '/patient/'+patient_id+'/encounter/start',
			'data' : $.param(data),
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


		this.stopEncounter = function(encounter_id){

					var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/encounter/"+encounter_id+"/stop",
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;


		};


		this.addEventSummary = function(form){


		var deferred = $q.defer();


		form.csrfmiddlewaretoken = this.csrf_token();
		

		$http({

			'method':'POST',
			'url' : '/encounter/add/event_summary',
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


		this.fetchPainAvatars = function(patient_id){

			var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/patient/"+patient_id+"/pain_avatars",
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;


		};


		this.listTerms = function(query){

			var data = {'query':query};

			var deferred = $q.defer();

			$http({
				"method":"GET",
				"url" : "/list_terms/",
				'params':data
			}).success(function(data){

				deferred.resolve(data);

			}).error(function(data){

				deferred.resolve(data);
			})

			return deferred.promise;

		};


		this.addGoal = function(form){


			var deferred = $q.defer();


			//form.csrfmiddlewaretoken = this.csrf_token();
		

		$http({

			'method':'POST',
			'url' : '/patient/'+form.patient_id+'/goals/add/new_goal',
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


		this.addToDo = function(form){


			var deferred = $q.defer();


			//form.csrfmiddlewaretoken = this.csrf_token();
		

		$http({

			'method':'POST',
			'url' : '/patient/'+form.patient_id+'/todos/add/new_todo',
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


		this.addProblem = function(form){


			var deferred = $q.defer();
			//form.csrfmiddlewaretoken = this.csrf_token();
		
			$http({
				'method':'POST',
				'url' : '/patient/'+form.patient_id+'/problems/add/new_problem',
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


		this.updatePatientSummary = function(form){


			var deferred = $q.defer();


			//form.csrfmiddlewaretoken = this.csrf_token();
		

		$http({

			'method':'POST',
			'url' : '/patient/'+form.patient_id+'/profile/update_summary',
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