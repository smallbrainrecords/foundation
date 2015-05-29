(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('ProblemsCtrl', function($scope, $routeParams, patientService, ngDialog){


			var patient_id = $('#patient_id').val();

			var problem_id = $routeParams.problem_id;
			patientService.fetchProblemInfo(problem_id).then(function(data){

                    $scope.problem = data['info'];

                    $scope.patient_notes = data['patient_notes'];
                    $scope.physician_notes = data['physician_notes'];

                    $scope.problem_goals = data['problem_goals'];
                    $scope.problem_todos = data['problem_todos'];

                    $scope.problem_images = data['problem_images'];
                    $scope.problem_relationships = data['problem_relationships'];
            });





			






		}); /* End of controller */


})();