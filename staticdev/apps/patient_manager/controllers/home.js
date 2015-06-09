(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('HomeCtrl', function($scope, $routeParams, patientService, ngDialog, toaster){


			var patient_id = $('#patient_id').val();


			$scope.patient_id = patient_id;
			
			patientService.fetchPatientInfo(patient_id).then(function(data){
				$scope.patient_info = data['info'];

				$scope.problems = data['problems'];

				$scope.goals = data['goals'];

				$scope.pending_todos = data['pending_todos'];
				$scope.accomplished_todos = data['accomplished_todos'];

				$scope.encounters = data['encounters'];


			});


			patientService.fetchPainAvatars(patient_id).then(function(data){

				$scope.pain_avatars = data['pain_avatars'];

			});


			$scope.update_patient_summary = function(){

					var form = {
						'patient_id': $scope.patient_id,
						'summary' : $scope.patient_info.summary
					};

					patientService.updatePatientSummary(form).then(function(data){

						toaster.pop('success', 'Done', 'Patient summary updated!');

					});

			};


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




			$scope.add_goal = function(form){

				form.patient_id = $scope.patient_id;
				patientService.addGoal(form).then(function(data){

					
					var new_goal = data['goal'];

					$scope.goals.push(new_goal);

					toaster.pop('success', "Done", "New goal created successfully!");
					console.log('pop');
					
				});
				
			}


			$scope.add_todo = function(form){

				form.patient_id = $scope.patient_id;

				patientService.addToDo(form).then(function(data){

					
					var new_todo = data['todo'];
					$scope.pending_todos.push(new_todo);
					toaster.pop('success', 'Done', 'New Todo added successfully');

				});

			};




			$scope.$watch('new_problem.name', function(newVal, oldVal){

				if (newVal==undefined){
					return false;
				}		

				if(newVal.length>2){

					patientService.listTerms(newVal).then(function(data){

						// console.log(data);
					});
				}

			});



			






		}); /* End of controller */


})();