(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('AddDifferentOrderCtrl', function($scope, $routeParams, observationService, ngDialog, problemService, toaster){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			$scope.observation_id = $routeParams.observation_id;

			observationService.fetchObservationInfo($scope.observation_id).then(function(data){
                $scope.observation = data['info'];
            });

            $scope.add_todo = function(form) {
            	if(form==undefined){
					return false;
				}

				if(form.name.trim().length<1){
					return false;
				}

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.observation.problem.id;
				form.observation_id = $scope.observation.id;
				problemService.addTodo(form).then(function(data){
					form.name = '';
					toaster.pop('success', 'Done', 'Added Todo!');
				});
            }



		})
		.controller('EnterNewValueCtrl', function($scope, $routeParams, observationService, ngDialog, problemService, toaster, patientService){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			$scope.observation_id = $routeParams.observation_id;

			observationService.fetchObservationInfo($scope.observation_id).then(function(data){
                $scope.observation = data['info'];
            });

            patientService.fetchActiveUser().then(function(data){

				$scope.active_user = data['user_profile'];

			});

            $scope.addValue = function(value) {
            	if(value==undefined) {
            		toaster.pop('error', 'Error', 'Please enter float value!');
            		return false;
            	}
            	if(isNaN(parseFloat(value.value))) {
            		toaster.pop('error', 'Error', 'Please enter float value!');
            		return false;
            	}

            	if(value.date==undefined) {
            		value.date = moment().format("YYYY-MM-DD");
            	}
            	value.observation_id = $scope.observation_id;
            	observationService.addNewValue(value).then(function(data){
	                toaster.pop('success', 'Done', 'Added New value!');
	            });
            };

            $scope.addValueRefused = function(value) {
            	if(value==undefined) {
            		toaster.pop('error', 'Error', 'Please enter float value!');
            		return false;
            	}
            	if(isNaN(parseFloat(value.value))) {
            		toaster.pop('error', 'Error', 'Please enter float value!');
            		return false;
            	}

            	if(value.date==undefined) {
            		value.date = moment().format("YYYY-MM-DD");
            	}
            	value.patient_refused_A1C = true;
            	value.observation_id = $scope.observation_id;
            	observationService.addNewValue(value).then(function(data){
	                toaster.pop('success', 'Done', 'Added New value!');
	            });
            };

            $scope.add_note = function(form) {
                if (form.note == '') return;
                form.observation_id = $scope.observation_id;
                observationService.addNote(form).then(function(data) {
                    $scope.observation.observation_notes.push(data['note']);
                    form.note = '';
                    toaster.pop('success', 'Done', 'Added Note!');
                });
            }

            $scope.toggleEditNote = function(note) {
                note.edit = true;
            }

            $scope.toggleSaveNote = function(note) {
                observationService.editNote(note).then(function(data) {
                    note.edit = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            }

            $scope.deleteNote = function(note) {
                observationService.deleteNote(note).then(function(data){
                    var index = $scope.observation.observation_notes.indexOf(note);
                    $scope.observation.observation_notes.splice(index, 1);
                    toaster.pop('success', 'Done', 'Deleted note successfully');
                });
            }

		}); /* End of controller */


})();