(function(){

	'use strict';


	angular.module('StaffApp')
		.controller('HomeCtrl', function($scope, $routeParams, ngDialog, staffService, physicianService, toaster, todoService, prompt){



			$scope.init = function(){
				var user_id = $('#user_id').val();
				$scope.user_id = user_id;

				staffService.getPatientsList().then(function(data){
					$scope.patients_list = data['patients_list'];
				});

				$scope.users = [];
				$scope.new_list = {};
				$scope.new_list.labels = [];
				$scope.todo_lists = [];
				$scope.currentLabel = null;


				staffService.fetchActiveUser().then(function(data){

					$scope.active_user = data['user_profile'];

					var role_form = {

						'actor_role':$scope.active_user.role,
						'actor_id':$scope.active_user.user.id
					}

					if($scope.active_user.role=='physician'){
						physicianService.getUsersList(role_form).then(function(data){
							$scope.users = data;
						});

						var form = {'physician_id':$scope.active_user.user.id};
						physicianService.getPhysicianData(form).then(function(data){

							$scope.patients = data['patients'];
							$scope.team = data['team'];
							
						});
					}

				});

				staffService.getUserTodoList(user_id).then(function(data){
					$scope.tagged_todos = data['tagged_todos'];
					$scope.personal_todos = data['personal_todos'];
					$scope.todos_ready = true;
				});

				todoService.fetchTodoMembers($scope.user_id).then(function(data){
	                $scope.members = data['members'];
	            });

	            todoService.fetchLabels($scope.user_id).then(function(data){
	                $scope.labels = data['labels'];
	            });

	            staffService.fetchLabeledTodoList($scope.user_id).then(function(data){
	                $scope.todo_lists = data['todo_lists'];
	            });
			};

			$scope.add_todo = function(form){

				form.user_id = $scope.user_id;

				staffService.addToDo(form).then(function(data){
					var new_todo = data['todo'];
					$scope.personal_todos.push(new_todo);
					$scope.new_todo = {};
					toaster.pop('success', 'Done', 'New Todo added successfully');
				});

			};

			$scope.add_new_list_label = function(new_list, label) {
				var index = new_list.labels.indexOf(label);
				if (index > -1)
					new_list.labels.splice(index, 1);
				else
					new_list.labels.push(label);
			};

			$scope.add_todo_list = function(form){

				form.user_id = $scope.user_id;
				if (form.name && form.labels.length > 0)
				{
					staffService.addToDoList(form).then(function(data){
						var new_list = data['new_list'];
						$scope.todo_lists.push(new_list);
						$scope.new_list = {};
						$scope.new_list.labels = [];
						toaster.pop('success', 'Done', 'New Todo List added successfully');
					});
				} else {
					toaster.pop('error', 'Error', 'Please select name and labels');
				}
			};

			$scope.delete_list = function(list) {
				prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a todo list is forever. There is no undo."
                }).then(function(result){
                    staffService.deleteToDoList(list).then(function(data){
						var index = $scope.todo_lists.indexOf(list);
						$scope.todo_lists.splice(index, 1);
						toaster.pop('success', 'Done', 'Todo List removed successfully');
					});
                },function(){
                    return false;
                });
			}


			$scope.init();

		}); /* End of controller */


})();