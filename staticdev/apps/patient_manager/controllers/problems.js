(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('ProblemsCtrl', function($scope, $routeParams, patientService, problemService, ngDialog, toaster){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var problem_id = $routeParams.problem_id;

			$scope.problem_id = problem_id;

			$scope.loading = true;

			patientService.fetchProblemInfo(problem_id).then(function(data){

                    $scope.problem = data['info'];

                    $scope.patient_notes = data['patient_notes'];
                    $scope.physician_notes = data['physician_notes'];

                    $scope.problem_goals = data['problem_goals'];
                    $scope.problem_todos = data['problem_todos'];

                    $scope.problem_images = data['problem_images'];
                    $scope.problem_relationships = data['problem_relationships'];

                    $scope.not_related_problems = data['not_related_problems'];

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

			$scope.unrelate = function(relationship){

				var c = confirm("Are you sure ?");

				if(c==false){
					return false;
				}
				var form = {};
				form.problem_id = $scope.problem.id;
				form.relationship_id = relationship.id;

				problemService.unRelateProblem(form).then(function(data){
					var relationship_index = $scope.problem_relationships.indexOf(relationship);
					$scope.problem_relationships.splice(relationship_index, 1);

					$scope.not_related_problems.push(relationship.target);

					toaster.pop('success', "Done", "Problem relationship removed !");
				});

			};

			$scope.relate_problem = function(problem){

				var c = confirm("Are you sure ?");

				if(c==false){
					return false;
				}

				var form = {};
				form.problem_id = $scope.problem_id;
				form.target_problem_id = problem.id;

				problemService.relateProblem(form).then(function(data){

					var problem_index = $scope.not_related_problems.indexOf(problem);
					$scope.not_related_problems.splice(problem_index, 1);

					$scope.problem_relationships.push(data['relationship']);

					toaster.pop('success', "Done", "Added problem relationship!");

				});

			};

			$scope.update_todo_status = function(todo){

				patientService.updateTodoStatus(todo).then(function(data){

					if(data['success']==true){

						console.log('updated');	
					}else{
						alert("Something went wrong!");
					}
					
				});				

			}

		}); /* End of controller */


})();