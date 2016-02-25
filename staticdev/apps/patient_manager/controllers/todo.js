(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('TodoCtrl', function($scope, $routeParams, $interval, patientService, ngDialog, todoService, toaster){

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var todo_id = $routeParams.todo_id;

			$scope.todo_id = todo_id;

			todoService.fetchTodoInfo(todo_id).then(function(data){
                $scope.todo = data['info'];
                $scope.comments = data['comments'];
                $scope.attachments = data['attachments'];
                $scope.related_encounters = data['related_encounters'];
                $scope.activities = data['activities'];
            });

            patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];
			});

			todoService.addTodoAccessEncounter(todo_id).then(function() {});

            todoService.fetchTodoMembers($scope.patient_id).then(function(data){
                $scope.members = data['members'];
            });


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
            	angular.element('#deleteCommentModal').modal();
            }

            $scope.confirmDelete = function(currentComment) {
            	todoService.deleteComment(currentComment).then(function(data){
					var index = $scope.comments.indexOf(currentComment);
					$scope.comments.splice(index, 1);
					angular.element('#deleteCommentModal').modal('hide');
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
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
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

            $scope.changeLabel2 = function(todo) {
                todo.change_label2 = (todo.change_label2 != true) ? true : false;
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
                            toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
                } else {
                    todo.labels.splice(existed_key, 1);
                    todoService.removeTodoLabel(existed_id).then(function(data){
                        if(data['success']==true){
                            toaster.pop('success', "Done", "Removed Todo label!");
                        }else{
                        	toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
                }
                
            }

            // change due date
            $scope.changeDueDate = function(todo) {
                todo.change_due_date = (todo.change_due_date != true) ? true : false;
            }

            $scope.changeDueDate2 = function(todo) {
                todo.change_due_date2 = (todo.change_due_date2 != true) ? true : false;
            }

            $scope.saveTodoDueDate = function(todo) {
                todoService.changeTodoDueDate(todo).then(function(data){
                    toaster.pop('success', "Done", "Due date Updated!");
                });
            }

            // Attachment
            $scope.changeAttachment = function(todo) {
                todo.change_attachment = (todo.change_attachment != true) ? true : false;
            }

            $scope.addAttachment = function(todo, attachment) {
            	var form = {};
				form.todo_id = $scope.todo_id;

				todoService.addAttachment(form, attachment).then(function(data){
					if(data['success']==true){
						toaster.pop('success', 'Done', 'Attachment uploaded!');
						var attachment = data['attachment'];
						console.log($scope.attachments);
						$scope.attachments.push(attachment);
					}else if(data['success']==false){
						toaster.pop('error', 'Error', 'Please fill valid data');
					}else{
						toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
					}
					todo.change_attachment = false
				});
            }

            // delete Attachment
            $scope.deleteAttachment = function(attachment) {
                $scope.currentAttachment = attachment;
                angular.element('#deleteAttachmentModal').modal();
            }

            $scope.confirmDeleteAttachment = function(currentAttachment) {
                todoService.deleteAttachment(currentAttachment).then(function(data){
                    var index = $scope.attachments.indexOf(currentAttachment);
                    $scope.attachments.splice(index, 1);
                    angular.element('#deleteAttachmentModal').modal('hide');
                    toaster.pop('success', 'Done', 'Deleted attachment successfully');
                });
            }

            $scope.refresh_todo_activity=function(){
                todoService.getTodoActivity($scope.todo_id).then(function(data){
                    if ($scope.activities.length != data['activities'].length)
                        $scope.activities = data['activities'];
                })
            }

            $interval(function(){
                $scope.refresh_todo_activity();
            }, 4000);

		}); /* End of controller */


})();