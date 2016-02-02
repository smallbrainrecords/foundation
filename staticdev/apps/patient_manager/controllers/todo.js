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
				console.log($scope.active_user);
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

		}); /* End of controller */


})();