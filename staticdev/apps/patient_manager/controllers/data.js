(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('DataCtrl', function($scope, $routeParams, ngDialog, problemService, toaster, $location, dataService){

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			$scope.data_id = $routeParams.data_id;

            dataService.fetchDataInfo($scope.data_id).then(function(data){
                $scope.data = data['info'];
            });

			
        }); /* End of controller */
})();