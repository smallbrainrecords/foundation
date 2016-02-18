(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('TodoCtrl', function($scope, $routeParams, patientService, ngDialog, todoService, toaster){

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var todo_id = $routeParams.todo_id;

			$scope.todo_id = todo_id;

			todoService.fetchTodoInfo(todo_id).then(function(data){
                $scope.todo = data['info'];
                $scope.comments = data['comments'];
            });

            patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];
			});

			todoService.addTodoAccessEncounter(todo_id).then(function() {});


            // add comment
            $scope.add_comment = function(form) {
            	form.todo_id = $scope.todo_id;

				todoService.addComment(form).then(function(data){
					var comment = data['comment'];
					$scope.comments.push(comment);

					$scope.new_comment = {};
					toaster.pop('success', 'Done', 'New Comment added successfully');
				});
            }

            // edit comment
            $scope.toggleEditComment = function(comment) {
            	comment.edit = true;
            }

            $scope.toggleSaveComment = function(comment) {

				todoService.editComment(comment).then(function(data){
					comment.datetime = data['comment']['datetime'];
					comment.edit = false;
					toaster.pop('success', 'Done', 'Edited comment successfully');
				});
            	
            }

            // delete comment
            $scope.delete = function(comment) {
            	$scope.currentComment = comment;
            	angular.element('#menuModal').modal();
            }

            $scope.confirmDelete = function(currentComment) {
            	todoService.deleteComment(currentComment).then(function(data){
					var index = $scope.comments.indexOf(currentComment);
					$scope.comments.splice(index, 1);
					angular.element('#menuModal').modal('hide');
					toaster.pop('success', 'Done', 'Deleted comment successfully');
				});
            }

            // change todo text
            $scope.changeText = function(todo) {
                todo.change_text = (todo.change_text != true) ? true : false;
            }

            $scope.saveTodoText = function(todo) {
                todoService.changeTodoText(todo).then(function(data){
                    if(data['success']==true){
                        toaster.pop('success', "Done", "Updated Todo text!");
                    }else{
                        alert("Something went wrong!");
                    }
                });
            }

            // change label
            // label
            $scope.labels = [
                {name: 'green', css_class: 'todo-label-green'},
                {name: 'yellow', css_class: 'todo-label-yellow'},
                {name: 'orange', css_class: 'todo-label-orange'},
                {name: 'red', css_class: 'todo-label-red'},
                {name: 'purple', css_class: 'todo-label-purple'},
                {name: 'blue', css_class: 'todo-label-blue'},
                {name: 'sky', css_class: 'todo-label-sky'},
            ];
            $scope.changeLabel = function(todo) {
                todo.change_label = (todo.change_label != true) ? true : false;
            }

            $scope.changeTodoLabel = function(todo, label) {

                var is_existed = false;
                var existed_key;
                var existed_id;

                angular.forEach(todo.labels, function(value, key) {
                    if (value.name==label.name) {
                        is_existed = true;
                        existed_key = key;
                        existed_id = value.id;
                    }
                });
                if (!is_existed) {
                    todo.labels.push(label);
                    todo.label_name = label.name;
                    todo.label_css_class = label.css_class;
                    todoService.addTodoLabel(todo).then(function(data){
                        if(data['success']==true){
                            toaster.pop('success', "Done", "Added Todo label!");
                        }else{
                            alert("Something went wrong!");
                        }
                    });
                } else {
                    todo.labels.splice(existed_key, 1);
                    todoService.removeTodoLabel(existed_id).then(function(data){
                        if(data['success']==true){
                            toaster.pop('success', "Done", "Removed Todo label!");
                        }else{
                            alert("Something went wrong!");
                        }
                    });
                }
                
            }

            // change due date
            $scope.changeDueDate = function(todo) {
                todo.change_due_date = (todo.change_due_date != true) ? true : false;
            }

            $scope.saveTodoDueDate = function(todo) {
                todoService.changeTodoDueDate(todo).then(function(data){
                });
            }

		}); /* End of controller */


})();