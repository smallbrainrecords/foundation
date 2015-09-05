(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('EncountersMainCtrl', function(
			$scope, $routeParams, patientService, ngDialog, $location){


			var patient_id = $('#patient_id').val();

			$scope.show_encounter_ui = false;

			$scope.patient_id = patient_id;


			$scope.encounter_flag = false;

			/* Get Status of any running encounters */

			patientService.getEncounterStatus(patient_id).then(function(data){

				$scope.show_encounter_ui = data['permitted'];

				if(data['encounter_active']==true){
					$scope.encounter_flag = true;
					$scope.encounter = data['current_encounter'];
				}else{
					$scope.encounter_flag = false;
				}


			});


			




			$scope.start_encounter = function(){

				if($scope.encounter_flag==true){
					alert("An encounter is already running!");
				}else{
					/* Send Request is Backend */
					
					patientService.startNewEncounter($scope.patient_id).then(function(data){

						alert('New Encounter Started');
						$scope.encounter = data['encounter'];
						$scope.encounter_flag = true;

					});
				}
			}


			
			$scope.stop_encounter = function(){


				if($scope.encounter_flag==true){
					var encounter_id = $scope.encounter.id;

					patientService.stopEncounter(encounter_id).then(function(data){

						if(data['success']==true){
							alert(data['msg']);
							/* Encounter Stopped */
							$scope.encounter_flag = false;
						}else{

							alert(data['msg']);
						}

					});
				}
			}
			

			$scope.view_encounter = function(){

				var encounter_id = $scope.encounter.id
				$location.path('/encounter/'+encounter_id);

			}


			$scope.add_event_summary = function(){

				if($scope.event_summary.length<1){

					alert("Please enter summary");
					return false;
				}

				var form = {
					'event_summary': $scope.event_summary,
					'encounter_id': $scope.encounter.id
				}

				patientService.addEventSummary(form).then(function(data){

					if(data['success']==true){
						console.log("Added event summary");

						$scope.event_summary = '';
					}else{
						alert("Failed");
					}

				});
			}


			


		}); /* End of controller */


})();