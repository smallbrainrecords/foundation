(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('ProblemsCtrl', function($scope, $routeParams, patientService, problemService, ngDialog, toaster){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var problem_id = $routeParams.problem_id;

			$scope.loading = true;

			patientService.fetchProblemInfo(problem_id).then(function(data){

                    $scope.problem = data['info'];

                    $scope.patient_notes = data['patient_notes'];
                    $scope.physician_notes = data['physician_notes'];

                    $scope.problem_goals = data['problem_goals'];
                    $scope.problem_todos = data['problem_todos'];

                    $scope.problem_images = data['problem_images'];
                    $scope.problem_relationships = data['problem_relationships'];

                    $scope.loading = false;
            });



			/* Track Status */

			$scope.$watch('[problem.is_controlled,problem.is_authenticated, problem.is_active]', function(nV, oV){

				if($scope.loading==true){
					return false;
				}

				if(angular.equals(oV, [undefined, undefined, undefined])==true){
					return false;
				}

				

				var form = {};

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				form.is_controlled = $scope.problem.is_controlled;
				form.is_authenticated = $scope.problem.is_authenticated;
				form.is_active = $scope.problem.is_active;


				problemService.updateProblemStatus(form).then(function(data){

					toaster.pop('success', 'Done', 'Updated Problem Status');

				});

			});


			/* TODO */

			$scope.update_start_date = function(){

				var form = {};

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				form.start_date = $scope.problem.start_date;

				problemService.updateStartDate(form).then(function(data){

					toaster.pop('success', 'Done', 'Updated Start Date');

				});
			}

			$scope.add_patient_note = function(form){

				if(form==undefined){
					return false;
				}

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				problemService.addPatientNote(form).then(function(data){

					$scope.patient_notes.unshift(data['note']);

					toaster.pop('success', 'Done','Added Patient Note!');
				});

			}

			$scope.add_physician_note = function(form){

				if(form==undefined){
					return false;
				}

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				problemService.addPhysicianNote(form).then(function(data){

					$scope.physician_notes.unshift(data['note']);
					toaster.pop('success', 'Done', 'Added Physician Note!');
				});
			}


			$scope.add_goal = function(form){

				if(form==undefined){
					return false;
				}

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				problemService.addGoal(form).then(function(data){

					$scope.problem_goals.push(data['goal']);
					toaster.pop('success', 'Done', 'Added Goal!');
				});
			}

			$scope.add_todo = function(form){


				if(form==undefined){
					return false;
				}

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				problemService.addTodo(form).then(function(data){

					$scope.problem_todos.push(data['todo']);
					toaster.pop('success', 'Done', 'Added Todo!');
				});
			}







		}); /* End of controller */


})();