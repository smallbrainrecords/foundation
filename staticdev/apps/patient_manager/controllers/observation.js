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
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function(result){
                    observationService.deleteNote(note).then(function(data){
                        var index = $scope.observation.observation_notes.indexOf(note);
                        $scope.observation.observation_notes.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted note successfully');
                    });
                },function(){
                    return false;
                });
            }

		})
        .controller('EditOrDeleteValuesCtrl', function($scope, $routeParams, observationService, ngDialog, problemService, toaster, patientService, prompt){


            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.observation_id = $routeParams.observation_id;

            patientService.fetchActiveUser().then(function(data){
                $scope.active_user = data['user_profile'];
            });

            observationService.fetchObservationInfo($scope.observation_id).then(function(data){
                $scope.observation = data['info'];
            });

            $scope.deleteValue = function(component) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a value is forever. There is no undo."
                }).then(function(result){
                    observationService.deleteValue(component).then(function(data){
                        var index = $scope.observation.observation_components.indexOf(component);
                        $scope.observation.observation_components.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted value successfully');
                    });
                },function(){
                    return false;
                });
            };

        })
        .controller('EditValueCtrl', function($scope, $routeParams, observationService, ngDialog, problemService, toaster, patientService, prompt, $location){


            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.component_id = $routeParams.component_id;

            patientService.fetchActiveUser().then(function(data){
                $scope.active_user = data['user_profile'];
            });

            observationService.fetchObservationComponentInfo($scope.component_id).then(function(data){
                $scope.component = data['info'];
                $scope.observation_id = data['observation_id'];
                $scope.today = moment();
                $scope.a1c_date = moment($scope.component.effective_datetime);
                $scope.a1c_date_format = moment($scope.component.effective_datetime).format("YYYY-MM-DD");
            });

            $scope.deleteValue = function(component) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a value is forever. There is no undo."
                }).then(function(result){
                    observationService.deleteValue(component).then(function(data){
                        toaster.pop('success', 'Done', 'Deleted value successfully');
                        $location.url('/observation/' + $scope.observation_id + '/edit_or_delete_values');
                    });
                },function(){
                    return false;
                });
            };

            $scope.editValue = function(component_id, value_quantity, effective_datetime) {
                if(isNaN(parseFloat(value_quantity))) {
                    toaster.pop('error', 'Error', 'Please enter float value!');
                    return false;
                }

                if(!moment(effective_datetime, "YYYY-MM-DD", true).isValid()) {
                    toaster.pop('error', 'Error', 'Please enter a valid date!');
                    return false;
                }
                var form = {};
                form.component_id = component_id;
                form.value_quantity = value_quantity;
                form.effective_datetime = effective_datetime;
                observationService.editValue(form).then(function(data){
                    $scope.component = data['info'];
                    $scope.a1c_date = moment($scope.component.effective_datetime);
                    $scope.a1c_date_format = moment($scope.component.effective_datetime).format("YYYY-MM-DD");
                    toaster.pop('success', 'Done', 'Edited value successfully');
                });
            }

            $scope.add_note = function(form) {
                if (form.note == '') return;
                form.component_id = $scope.component_id;
                observationService.addComponentNote(form).then(function(data) {
                    $scope.component.observation_component_notes.push(data['note']);
                    form.note = '';
                    toaster.pop('success', 'Done', 'Added Note!');
                });
            }

            $scope.toggleEditNote = function(note) {
                note.edit = true;
            }

            $scope.toggleSaveNote = function(note) {
                observationService.editComponentNote(note).then(function(data) {
                    note.edit = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            }

            $scope.deleteNote = function(note) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function(result){
                    observationService.deleteComponentNote(note).then(function(data){
                        var index = $scope.component.observation_component_notes.indexOf(note);
                        $scope.component.observation_component_notes.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted note successfully');
                    });
                },function(){
                    return false;
                });
            }

        }); /* End of controller */


})();