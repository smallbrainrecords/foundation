(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('HomeCtrl', function($scope, $routeParams, patientService){


			var patient_id = $('#patient_id').val();

			patientService.fetchPatientInfo(patient_id).then(function(data){
				$scope.patient_info = data['info'];

				$scope.problems = data['problems'];
			});
			

			

			$scope.goals = {};

			$scope.todos = {};

			$scope.encounters = {};




		}); /* End of controller */


})();