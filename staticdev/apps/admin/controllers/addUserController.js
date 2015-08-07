(function(){

	'use strict';


	angular.module('AdminApp')
		.controller('AddUserCtrl', function(
			$scope, $routeParams, ngDialog, 
			adminService, $location, $anchorScroll, toaster){




			$scope.add_user = function(){

				
				var form = $scope.form;
				adminService.addUser(form).then(function(data){

					if(data['success']==true){
						alert("User is created");
						$location.path('/');
					}else if(data['success']==false){
						
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