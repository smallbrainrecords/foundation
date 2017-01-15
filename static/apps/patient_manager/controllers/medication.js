(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('MedicationCtrl', function ($scope, $routeParams, ngDialog, problemService, sharedService,
                                                toaster, $location, patientService, $filter, medicationService, prompt) {
            // Properties
            $scope.user_id = $('#user_id').val();
            $scope.patient_id = $('#patient_id').val();
            $scope.showMedicationSearch = false;
            $scope.show_medication_history = false;
            $scope.medication_id = $routeParams.medication_id;
            // Containing edit history of this medication record including: Status changing, Dosage changing and note changing, pinned problem
            $scope.medicationHistory = [];
            $scope.medicationNoteHistory = [];
            $scope.show_pin_to_new_problem = false;

            $scope.init = init;
            $scope.see_medication_history = see_medication_history;
            $scope.add_note = add_note;
            $scope.isInPins = isInPins;
            $scope.toggle_pin_to_new_problem = toggle_pin_to_new_problem;
            $scope.medication_pin_to_problem = medication_pin_to_problem;
            $scope.open_problem = open_problem;
            $scope.change_active_medication = change_active_medication;
            $scope.changeDosage = changeDosage;
            $scope.updateNoteHistory = updateNoteHistory;
            $scope.deleteNoteHistory = deleteNoteHistory;

            // Method definition
            function init() {
                //sharedService.initHotkey($scope);

                patientService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });

                medicationService.fetchMedicationInfo($scope.patient_id, $scope.medication_id).then(function (data) {
                    $scope.medication = data['info'];
                    $scope.medicationHistory = data['history'];
                    $scope.medicationNoteHistory = data['noteHistory'];
                });

                // pin to problem
                problemService.fetchProblems($scope.patient_id).then(function (data) {
                    $scope.problems = data['problems'];

                    medicationService.fetchPinToProblem($scope.medication_id).then(function (data) {
                        $scope.pins = data['pins'];

                        angular.forEach($scope.problems, function (problem) {
                            if ($scope.isInPins($scope.pins, problem)) {
                                problem.pin = true;
                            }
                        });
                    });
                });
            }

            function see_medication_history() {
                $scope.medication.show_medication_history = !$scope.medication.show_medication_history;
            }

            function add_note(form, oldNote) {
                if (form.note == '') return;
                form.medication_id = $scope.medication.id;
                form.patient_id = $scope.patient_id;
                medicationService.addMedicationNote(form).then(function (data) {
                    $scope.medicationNoteHistory.push(data['note']);
                    if (typeof oldNote !== 'undefined')
                        form.note = oldNote;
                    toaster.pop('success', 'Done', 'Added note!');
                });
            }

            function isInPins(array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value.problem == item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            }

            function toggle_pin_to_new_problem() {
                $scope.show_pin_to_new_problem = !$scope.show_pin_to_new_problem;
            }

            function medication_pin_to_problem(medication_id, problem_id) {
                var form = {};
                form.medication_id = medication_id;
                form.problem_id = problem_id;

                medicationService.medicationPinToProblem($scope.patient_id, form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Pinned problem!');
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            }

            function open_problem(problem) {
                $location.path('/problem/' + problem.id);
            }

            function change_active_medication() {
                medicationService.changeActiveMedication($scope.patient_id, $scope.medication_id)
                    .then(function (response) {
                        toaster.pop('success', 'Done', 'Changed successfully!');
                    });
            }

            function changeDosage(medication) {
                medicationService.changeDosage($scope.patient_id, $scope.medication.id, medication)
                    .then(function (response) {
                        if (response.data.success) {
                            toaster.pop('success', 'Done', 'Changed successfully!');
                            $scope.showMedicationSearch = false;
                            $scope.medication = response.data.medication;
                            $scope.medicationHistory.unshift(response.data.history)
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
            }

            function updateNoteHistory(note) {
                medicationService.editNote(note)
                    .then(function (data) {
                        note.editMode = false;
                        toaster.pop('success', 'Done', 'Edited note successfully');
                    });
            }

            function deleteNoteHistory(note) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function (result) {
                    medicationService.deleteNote(note)
                        .then(function (data) {
                            var index = $scope.medicationNoteHistory.indexOf(note);
                            $scope.medicationNoteHistory.splice(index, 1);
                            toaster.pop('success', 'Done', 'Deleted note successfully');
                        });
                }, function () {
                    return false;
                });
            }

            $scope.init();
        });
    /* End of controller */
})();