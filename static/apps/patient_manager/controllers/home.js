(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('HomeCtrl', function($scope, $routeParams, patientService, ngDialog){


			var patient_id = $('#patient_id').val();

			patientService.fetchPatientInfo(patient_id).then(function(data){
				$scope.patient_info = data['info'];

				$scope.problems = data['problems'];

				$scope.goals = data['goals'];

				$scope.pending_todos = data['pending_todos'];
				$scope.accomplished_todos = data['accomplished_todos'];

				$scope.encounters = data['encounters'];
			});


			$scope.show_accomplished_todos = false;

			$scope.toggle_accomplished_todos  = function(){

				var flag = $scope.show_accomplished_todos;

				if(flag==true){
					flag = false;
				}else{
					flag=true;
				}

				$scope.show_accomplished_todos = flag;
			}


			$scope.add_problem = function(){

				alert("To be implemented");
				console.log($scope.new_problem);
			}

			$scope.add_todo = function(){

				alert("To be implemented");
				console.log($scope.new_todo);
			}


			$scope.add_goal = function(){

				alert("To be implemented");
				console.log($scope.new_goal);
			}

			$scope.show_problem = function(){


				ngDialog.open({
                        template: '/static/apps/patient_manager/partials/modals/show_problem.html',
                        className: 'ngdialog-theme-default large-modal',
                        scope: $scope,
                        cache: false,
                        controller: ['$scope',
                            function($scope) {

                            }]
                        });

			}


			$scope.show_goal = function(){


				ngDialog.open({
                        template: '/static/apps/patient_manager/partials/modals/show_goal.html',
                        className: 'ngdialog-theme-default large-modal',
                        scope: $scope,
                        cache: false,
                        controller: ['$scope',
                            function($scope) {

                            }]
                        });

			}


			






		}); /* End of controller */


})();