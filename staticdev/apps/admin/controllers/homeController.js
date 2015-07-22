(function(){

	'use strict';


	function loop(payload){

		payload();

		setTimeout(function(){
			loop(payload);
		}, 5000);

	};

	angular.module('AdminApp')
		.controller('HomeCtrl', function($scope, $routeParams, ngDialog, adminService){




			$scope.users = [];


			adminService.getUsersList().then(function(data){

				$scope.users = data;
			});

			adminService.getPendingRegistrationUsersList().then(function(data){

				$scope.pending_users = data;
			});


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


			

		}); /* End of controller */


})();