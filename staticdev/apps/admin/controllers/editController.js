(function(){

	'use strict';


	angular.module('AdminApp')
		.controller('EditCtrl', function($scope, $routeParams, ngDialog, adminService, $location, $anchorScroll){




			$scope.user_id = $routeParams['userId'];

			adminService.getUserInfo($scope.user_id).then(function(data){

				$scope.user_profile = data['user_profile'];

			});


			$scope.update_profile = function(){

				alert('To be Done');

			};


			$scope.navigate = function(l){
				/* Replace by directive */
				
				$("html, body").animate({ scrollTop: $('#'+l).offset().top-100 }, 500);
			};

		}); /* End of controller */


})();