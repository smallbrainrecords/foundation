(function () {
    'use strict';

    // TODO: Separate these controllers to separated files

    angular.module('ManagerApp')
        .controller('AddDifferentOrderCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                       sharedService, toaster, $location, patientService) {


            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.a1c_id = $routeParams.a1c_id;
            //sharedService.initHotkey($scope);

            a1cService.fetchA1cInfo($scope.a1c_id).then(function (data) {
                $scope.a1c = data['info'];
            });

            patientService.fetchPatientInfo($scope.patient_id).then(function (data) {
                $scope.patient = data;
            });

            $scope.add_todo = function (form) {
                if (form == undefined) {
                    return false;
                }

                if (form.month != '' && form.month != undefined) {
                    form.due_date = moment().add(form.month, "months").format("MM/DD/YYYY");
                    form.name = 'a1c repeats in ' + form.month + ' months';
                }

                if (form.name.trim().length < 1) {
                    return false;
                }

                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.a1c.problem.id;
                form.a1c_id = $scope.a1c.id;

                if ($scope.patient['bleeding_risk']) {
                    var bleedingRiskDialog = ngDialog.open({
                        template: 'bleedingRiskDialog',
                        showClose: false,
                        closeByEscape: false,
                        closeByDocument: false,
                        closeByNavigation: false
                    });

                    bleedingRiskDialog.closePromise.then(function () {
                        problemService.addTodo(form).then(addTodoSuccess);
                    });
                } else {
                    problemService.addTodo(form).then(addTodoSuccess);
                }

                // Add todo succeeded
                function addTodoSuccess(data) {
                    form.name = '';
                    form.month = '';
                    toaster.pop('success', 'Done', 'Added Todo!');
                    $location.url('/problem/' + $scope.a1c.problem.id);
                }
            }


        })
        .controller('EnterNewValueCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                   sharedService, toaster, patientService, $location) {


            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.a1c_id = $routeParams.a1c_id;
            //sharedService.initHotkey($scope);

            a1cService.fetchA1cInfo($scope.a1c_id).then(function (data) {
                $scope.a1c = data['info'];
            });

            patientService.fetchActiveUser().then(function (data) {

                $scope.active_user = data['user_profile'];

            });

            $scope.addValue = function (value) {
                if (value == undefined) {
                    toaster.pop('error', 'Error', 'Please enter float value!');
                    return false;
                }
                if (isNaN(parseFloat(value.value))) {
                    toaster.pop('error', 'Error', 'Please enter float value!');
                    return false;
                }

                if (value.date == undefined) {
                    value.date = moment().format("YYYY-MM-DD");
                }
                value.component_id = $scope.a1c.observation.observation_components[0].id;
                a1cService.addNewValue(value).then(function (data) {
                    toaster.pop('success', 'Done', 'Added New value!');
                    $location.url('/problem/' + $scope.a1c.problem.id);
                });
            };

            $scope.addValueRefused = function (value) {
                value = {};
                if (value.date == undefined) {
                    value.date = moment().format("YYYY-MM-DD");
                }
                value.patient_refused_A1C = true;
                value.a1c_id = $scope.a1c_id;
                a1cService.addValueRefused(value).then(function (data) {
                    toaster.pop('success', 'Done', 'Patient refused!');
                    $location.url('/problem/' + $scope.a1c.problem.id);
                });
            };

            $scope.add_note = function (form) {
                if (form.note == '') return;
                form.a1c_id = $scope.a1c_id;
                a1cService.addNote(form).then(function (data) {
                    $scope.a1c.a1c_notes.push(data['note']);
                    form.note = '';
                    toaster.pop('success', 'Done', 'Added Note!');
                });
            }

            $scope.toggleEditNote = function (note) {
                note.edit = true;
            }

            $scope.toggleSaveNote = function (note) {
                a1cService.editNote(note).then(function (data) {
                    note.edit = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            }

            $scope.deleteNote = function (note) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function (result) {
                    a1cService.deleteNote(note).then(function (data) {
                        var index = $scope.a1c.a1c_notes.indexOf(note);
                        $scope.a1c.a1c_notes.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted note successfully');
                    });
                }, function () {
                    return false;
                });
            }

        })
        .controller('EditOrDeleteValuesCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                        sharedService, toaster, patientService, prompt) {


            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.a1c_id = $routeParams.a1c_id;
            //sharedService.initHotkey($scope);

            patientService.fetchActiveUser().then(function (data) {
                $scope.active_user = data['user_profile'];
            });

            a1cService.fetchA1cInfo($scope.a1c_id).then(function (data) {
                $scope.a1c = data['info'];

                if ($scope.a1c.observation.observation_components.length > 0)
                    $scope.first_component = $scope.a1c.observation.observation_components[0];
            });

            $scope.deleteValue = function (value) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a value is forever. There is no undo."
                }).then(function (result) {
                    a1cService.deleteValue(value).then(function (data) {
                        var index = $scope.first_component.observation_component_values.indexOf(value);
                        $scope.first_component.observation_component_values.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted value successfully');
                    });
                }, function () {
                    return false;
                });
            };

        })
        .controller('EditValueCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                               sharedService, toaster, patientService, prompt, $location) {


            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.value_id = $routeParams.value_id;
            //sharedService.initHotkey($scope);
            patientService.fetchActiveUser().then(function (data) {
                $scope.active_user = data['user_profile'];
            });

            a1cService.fetchObservationValueInfo($scope.value_id).then(function (data) {
                $scope.value = data['info'];
                $scope.a1c_id = data['a1c_id'];
                $scope.today = moment();
                $scope.a1c_date = moment($scope.value.effective_datetime);
                $scope.a1c_date_format = moment($scope.value.effective_datetime).format("YYYY-MM-DD");
            });

            $scope.deleteValue = function (value) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a value is forever. There is no undo."
                }).then(function (result) {
                    a1cService.deleteValue(value).then(function (data) {
                        toaster.pop('success', 'Done', 'Deleted value successfully');
                        $location.url('/a1c/' + $scope.a1c_id + '/edit_or_delete_values');
                    });
                }, function () {
                    return false;
                });
            };

            $scope.editValue = function (value_id, value_quantity, effective_datetime) {
                if (isNaN(parseFloat(value_quantity))) {
                    toaster.pop('error', 'Error', 'Please enter float value!');
                    return false;
                }

                if (!moment(effective_datetime, "YYYY-MM-DD", true).isValid()) {
                    toaster.pop('error', 'Error', 'Please enter a valid date!');
                    return false;
                }
                var form = {};
                form.value_id = value_id;
                form.value_quantity = value_quantity;
                form.effective_datetime = effective_datetime;
                a1cService.editValue(form).then(function (data) {
                    $scope.value = data['info'];
                    $scope.a1c_date = moment($scope.value.effective_datetime);
                    $scope.a1c_date_format = moment($scope.value.effective_datetime).format("YYYY-MM-DD");
                    toaster.pop('success', 'Done', 'Edited value successfully');
                });
            }

            $scope.add_note = function (form) {
                if (form.note == '') return;
                form.value_id = $scope.value_id;
                a1cService.addValueNote(form).then(function (data) {
                    $scope.value.observation_value_notes.push(data['note']);
                    form.note = '';
                    toaster.pop('success', 'Done', 'Added Note!');
                });
            }

            $scope.toggleEditNote = function (note) {
                note.edit = true;
            }

            $scope.toggleSaveNote = function (note) {
                a1cService.editValueNote(note).then(function (data) {
                    note.edit = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            }

            $scope.deleteNote = function (note) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function (result) {
                    a1cService.deleteValueNote(note).then(function (data) {
                        var index = $scope.value.observation_value_notes.indexOf(note);
                        $scope.value.observation_value_notes.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted note successfully');
                    });
                }, function () {
                    return false;
                });
            }

        });
    /* End of controller */


})();