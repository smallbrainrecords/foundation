(function(){

	'use strict';


	angular.module('AdminApp')
		.controller('HomeCtrl', function($scope, $routeParams, ngDialog, adminService){



			$scope.init = function(){


				$scope.users = [];


				adminService.fetchActiveUser().then(function(data){

					$scope.active_user = data['user_profile'];

					var role_form = {

						'actor_role':$scope.active_user.role,
						'actor_id':$scope.active_user.user.id
					}


					adminService.getUsersList(role_form).then(function(data){
						$scope.users = data;
					});


					
					adminService.getPendingRegistrationUsersList(role_form).then(function(data){

						$scope.pending_users = data;
					});


					if($scope.active_user.role=='physician'){

						var form = {'physician_id':$scope.active_user.user.id};
						adminService.getPhysicianData(form).then(function(data){

							$scope.patients = data['patients'];
							$scope.team = data['team'];
							
						});



					}

				});
			};


			$scope.refresh_pending_users  = function(){

				adminService.getPendingRegistrationUsersList().then(function(data){
					$scope.pending_users = data;
				});

			};

			$scope.update_pending_user = function(user){

				if(user.role=='patient'||user.role=='physician'||user.role=='admin'){
					console.log(user);

					adminService.approveUser(user).then(function(data){
						
						var index = $scope.pending_users.indexOf(user);
						if(index>-1){

								$scope.pending_users.splice(index,1);

							
						}
					});


				}else{
					alert("Please assign role!");
				}

			};


			$scope.init();

		}); /* End of controller */


})();