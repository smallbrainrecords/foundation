(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('ProblemsCtrl', function($scope, $routeParams, patientService, problemService, ngDialog, toaster){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var problem_id = $routeParams.problem_id;

			$scope.problem_id = problem_id;

			$scope.loading = true;

			patientService.fetchActiveUser().then(function(data){

				$scope.active_user = data['user_profile'];

			});

			patientService.fetchProblemInfo(problem_id).then(function(data){

                    $scope.problem = data['info'];

                    console.log($scope.problem);

                    $scope.patient_notes = data['patient_notes'];
                    $scope.physician_notes = data['physician_notes'];

                    $scope.problem_goals = data['problem_goals'];
                    $scope.problem_todos = data['problem_todos'];

                    $scope.problem_images = data['problem_images'];

                    $scope.effecting_problems = data['effecting_problems'];
                    $scope.effected_problems = data['effected_problems'];

                    var patient_problems = data['patient_problems'];

                    


                    for(var index in patient_problems){

                    	var id = patient_problems[index].id;

                    	if ($scope.id_exists(id, $scope.effecting_problems)==true){
                    		patient_problems[index].effecting=true
                    	}

                    	if ($scope.id_exists(id, $scope.effected_problems)==true){
                    		patient_problems[index].effected=true
                    	}


                    }

                    $scope.patient_problems = patient_problems;

                    $scope.loading = false;
            });



			/* Track Status */

			$scope.$watch('[problem.is_controlled,problem.authenticated, problem.is_active]', function(nV, oV){

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
				form.authenticated = $scope.problem.authenticated;
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

					if(data['success']==true){

						$scope.patient_notes.unshift(data['note']);
						toaster.pop('success', 'Done','Added Patient Note!');


					}else{

						angular.forEach(data['errors'], function(value, key){
							alert(value);
						});

					}

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



			$scope.image_upload_url = function(){

				var patient_id = $scope.patient_id;
				var problem_id = $scope.problem_id;
				var url = '/p/patient/'+patient_id+'/problem/'+problem_id+'/upload_image';
				return url;
			}


			$scope.open_image_box = function(image){

				    ngDialog.open({
                        template:'/static/apps/patient_manager/partials/modals/image.html',
                        className:'ngdialog-theme-default large-modal',
                        scope:$scope,
                        cache:false,
                        controller: ['$scope',
                        function($scope){

                        	$scope.image = image;

                        }]
                    });

			};

			$scope.delete_problem_image = function(image){

				var c = confirm("Are you sure ?");

				if(c==false){
					return false;
				}

				var form = {};
				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				form.image_id = image.id;

				problemService.deleteProblemImage(form).then(function(data){

					var image_index = $scope.problem_images.indexOf(image);

					$scope.problem_images.splice(image_index, 1);
					toaster.pop('success', 'Done', 'Added Todo!');
				});
			};




			$scope.update_todo_status = function(todo){

				patientService.updateTodoStatus(todo).then(function(data){

					if(data['success']==true){

						toaster.pop('success', "Done", "Updated Todo status !");
					}else{
						alert("Something went wrong!");
					}
					
				});				

			}


			$scope.id_exists = function(id, item_list){

				var found = false;

				angular.forEach(item_list, function(value){
					
					if(value==id){
						found = true;
					}

				});

				return found;

			}


			$scope.change_effecting_problem = function(source, problem){

				var effecting = source.effecting;

				var form = {};
				form.source_id = source.id;
				form.target_id = problem.id;
				form.relationship = effecting;
				problemService.relateProblem(form).then(function(data){


				});

			}

			$scope.change_effected_problem = function(problem, target){

				
				var effected = target.effected;

				var form = {};
				form.source_id = problem.id;
				form.target_id = target.id;
				form.relationship = effected;

				problemService.relateProblem(form).then(function(data){


				});

			}



		}); /* End of controller */


})();