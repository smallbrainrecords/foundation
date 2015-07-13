(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('GoalsCtrl', function($scope, $routeParams, patientService, ngDialog, toaster, goalService){


			var patient_id = $('#patient_id').val();

			var goal_id = $routeParams.goal_id;

			$scope.goal_id = goal_id;
			$scope.patient_id = patient_id;

			$scope.loading = true;

			patientService.fetchGoalInfo(goal_id).then(function(data){

				$scope.goal = data['goal'];
				$scope.goal_notes = data['goal_notes'];
				$scope.loading = false;	

            });




			/* Track goal status */

			$scope.$watch('[goal.is_controlled,goal.accomplished]', function(newVal, oldVal){

				if($scope.loading==true){
					return false;
				}

				if(angular.equals(oldVal, [undefined, undefined])){
					return false;
				}

				var form = {};
				form.patient_id = $scope.patient_id;
				form.goal_id = $scope.goal_id;
				form.is_controlled = $scope.goal.is_controlled;
				form.accomplished = $scope.goal.accomplished;

				goalService.updateGoalStatus(form).then(function(data){

					toaster.pop('success', 'Done', 'Updated Goal Status');

				});


			});
			

			$scope.update_motivation = function(){

				var form = {};
				form.patient_id = $scope.patient_id;
				form.goal_id = $scope.goal_id;

				form.new_note = $scope.new_note;

				goalService.addNote(form).then(function(data){

					$scope.goal_notes.unshift(data['note']);

					toaster.pop('success', 'Done', 'Added Note');
				})


			};






		}); /* End of controller */


})();