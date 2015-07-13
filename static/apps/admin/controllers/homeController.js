(function(){

	'use strict';


	angular.module('AdminApp')
		.controller('HomeCtrl', function($scope, $routeParams, ngDialog, adminService){




			$scope.users = [];


			adminService.getUsersList().then(function(data){

				$scope.users = data;
			});


		}); /* End of controller */


})();