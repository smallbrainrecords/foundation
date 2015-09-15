(function(){

	'use strict';


	angular.module('ManagerApp').service('patientService',
		function($http, $q, $cookies, httpService){



		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};

		this.fetchPatientInfo = function(patient_id){

			var params = {};
			var url = '/u/patient/'+patient_id+'/info';

			return httpService.get(params, url);

		};


		this.fetchProblemInfo = function(problem_id){

			var url = "/p/problem/"+problem_id+"/info";
			var params = {};

			return httpService.get(params, url);

		};


		this.fetchGoalInfo = function(goal_id){

			var url = "/g/goal/"+goal_id+"/info"
			var params = {}

			return httpService.get(params, url);
		};


		this.fetchEncounterInfo = function(encounter_id){

			var url = "/enc/encounter/"+encounter_id+"/info"
			var params = {}

			return httpService.get(params, url);


		};



		this.getEncounterStatus = function(patient_id){

			var url = "/enc/patient/"+patient_id+"/encounter/status";
			var params = {}

			return httpService.get(params, url);

			

		};

		this.startNewEncounter = function(patient_id){


			var url = '/enc/patient/'+patient_id+'/encounter/start';
			var form = { 'patient_id':patient_id };

			return httpService.post(form, url);


		};


		this.stopEncounter = function(encounter_id){

			var url = "/enc/encounter/"+encounter_id+"/stop";
			var params = {}

			return httpService.get(params, url);


		};


		this.addEventSummary = function(form){

			var url = '/enc/encounter/add/event_summary';

			return httpService.post(form, url);

		};


		this.fetchPainAvatars = function(patient_id){

			var url = "/patient/"+patient_id+"/pain_avatars";
			var params = {};

			return httpService.get(params, url);


		};


		this.listTerms = function(query){

			var params = {'query':query};
			var url = "/list_terms/";

			return httpService.get(params, url);


		};


		this.addGoal = function(form){

			var url = '/g/patient/'+form.patient_id+'/goals/add/new_goal';

			return httpService.post(form, url);

		};


		this.addToDo = function(form){

			var url = '/todo/patient/'+form.patient_id+'/todos/add/new_todo';

			return httpService.post(form, url);



		};


		this.addProblem = function(form){

			var url = '/p/patient/'+form.patient_id+'/problems/add/new_problem';

			return httpService.post(form, url);


		};


		this.updatePatientSummary = function(form){

			var url = '/u/patient/'+form.patient_id+'/profile/update_summary';

			return httpService.post(form, url);

		};


		this.updateTodoStatus = function(form){

			var url = '/todo/todo/'+ form.id + '/update/';

			return httpService.post(form, url);


		};


		this.fetchActiveUser = function(){

			var url = '/u/active/user/';
			var params = {};

			return httpService.get(params, url);

			};

		});


})();