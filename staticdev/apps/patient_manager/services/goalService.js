(function(){

	'use strict';

	angular.module('ManagerApp').service('goalService',
		function($http, $q, $cookies, httpService){


		this.updateGoalStatus = function(form){

			var url = '/g/patient/'+form.patient_id+'/goal/'+form.goal_id+'/update_status';
			return httpService.post(form, url);

		};


		this.addNote = function(form){

			var url = '/g/patient/'+form.patient_id+'/goal/'+form.goal_id+'/add_note';
			return httpService.post(form, url);


		};


		});



})();