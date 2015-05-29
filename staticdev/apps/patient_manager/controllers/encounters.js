(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('EncountersCtrl', function($scope, $routeParams, patientService, ngDialog, $location){


			var patient_id = $('#patient_id').val();

			var encounter_id = $routeParams.encounter_id;

			patientService.fetchEncounterInfo(encounter_id).then(function(data){

				$scope.encounter = data['encounter'];
				$scope.encounter_events = data['encounter_events'];

            });





			






		}); /* End of controller */


})();