(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('EncountersCtrl', function($scope, $routeParams, patientService, ngDialog, $location, toaster, encounterService){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var encounter_id = $routeParams.encounter_id;
			$scope.encounter_id = encounter_id;

			patientService.fetchEncounterInfo(encounter_id).then(function(data){

				$scope.encounter = data['encounter'];
				$scope.encounter_events = data['encounter_events'];

            });


            $scope.update_note = function(){

            	var form = {};
            	form.encounter_id = $scope.encounter_id;
            	form.patient_id = $scope.patient_id;
            	form.note = $scope.encounter.note;
            	encounterService.updateNote(form).then(function(data){

            		toaster.pop('success', 'Done', 'Updated note!');

            	});


            };

            $scope.upload_video = function(){

				var form = {};
            	form.encounter_id = $scope.encounter_id;
            	form.patient_id = $scope.patient_id;
            	var file = $scope.video_file;

            	encounterService.uploadVideo(form, file).then(function(data){

            		if(data['success'] == true){

            			toaster.pop('success', 'Done', 'Uploaded Video!');
            		}
            	});

			};

			$scope.upload_audio = function(){

				var form = {};
            	form.encounter_id = $scope.encounter_id;
            	form.patient_id = $scope.patient_id;
            	var file = $scope.audio_file;

				encounterService.uploadAudio(form, file).then(function(data){

            		if(data['success'] == true){

            			toaster.pop('success', 'Done', 'Uploaded Audio!');
            		}
            	});

			};





		}); /* End of controller */


})();