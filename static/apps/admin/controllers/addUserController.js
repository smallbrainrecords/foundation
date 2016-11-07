(function(){

	'use strict';


	angular.module('AdminApp')
		.controller('AddUserCtrl', function(
			$scope, $routeParams, ngDialog, 
			adminService, $location, $anchorScroll, toaster){

			adminService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];
			});

			$scope.add_user = function(){
				var form = $scope.form;
				adminService.addUser(form).then(function(data){
					if(data['success']==true){
						alert("User is created");
						if ($scope.active_user.role == 'mid-level' || $scope.active_user.role == 'nurse' || $scope.active_user.role == 'secretary')
							location.href = '/u/staff/';
						else {
							$location.path('/');
						}
					}else if(data['success']==false){
						alert(data['msg']);
						angular.forEach(data['errors'], function(value){
							alert(value);
						});
					}else{
						alert("Something went wrong");
					}
				});

			}
		}); /* End of controller */


})();