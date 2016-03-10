(function(){

	'use strict';


	angular.module('StaffApp')
		.controller('HomeCtrl', function($scope, $routeParams, ngDialog, staffService){



			$scope.init = function(){
				staffService.getPatientsList().then(function(data){
					$scope.patients_list = data['patients_list'];
				});

			};


			$scope.init();

		}); /* End of controller */


})();