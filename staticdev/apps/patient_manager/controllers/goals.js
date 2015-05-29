(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('GoalsCtrl', function($scope, $routeParams, patientService, ngDialog){


			var patient_id = $('#patient_id').val();

			var goal_id = $routeParams.goal_id;

			patientService.fetchGoalInfo(goal_id).then(function(data){

				$scope.goal = data['goal'];
				

            });





			






		}); /* End of controller */


})();