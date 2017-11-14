(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('MedicationCtrl', function ($scope, $routeParams, ngDialog, problemService, sharedService,
                                                toaster, $location, patientService, $filter, medicationService, prompt) {

            $scope.showMedicationSearch = false;
            $scope.showMedicationHistory = false;
            $scope.medication_id = $routeParams.medication_id;
            $scope.medicationHistory = [];
            $scope.medicationNoteHistory = [];
            $scope.showPinToNewProblem = false;

            $scope.seeMedicationHistory = seeMedicationHistory;
            $scope.addNote = addNote;
            $scope.isInPins = isInPins;
            $scope.togglePinToNewProblem = togglePinToNewProblem;
            $scope.medicationPinToProblem = medicationPinToProblem;
            $scope.openProblem = openProblem;
            $scope.changeActiveMedication = changeActiveMedication;
            $scope.changeDosage = changeDosage;
            $scope.updateNoteHistory = updateNoteHistory;
            $scope.deleteNoteHistory = deleteNoteHistory;

            init();

            ////////////////////////

            function init() {

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

            function seeMedicationHistory() {
                $scope.medication.showMedicationHistory = !$scope.medication.showMedicationHistory;
            }

            function addNote(form, oldNote) {
                if (form.note == '')
                    return;

                form.medication_id = $scope.medication.id;
                form.patient_id = $scope.patient_id;

                medicationService.addMedicationNote(form)
                    .then(function (data) {
                        $scope.medicationNoteHistory.push(data['note']);
                        if (typeof oldNote !== 'undefined')
                            form.note = oldNote;
                        toaster.pop('success', 'Done', 'Added note!');
                    });
            }

            function isInPins(array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value.problem === item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            }

            function togglePinToNewProblem() {
                $scope.showPinToNewProblem = !$scope.showPinToNewProblem;
            }

            function medicationPinToProblem(medication_id, problem_id) {
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

            function openProblem(problem) {
                $location.path('/problem/' + problem.id);
            }

            function changeActiveMedication() {
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
                        if (data.success) {
                            note.editMode = false;
                            toaster.pop('success', 'Done', 'Edited note success');
                        } else {
                            toaster.pop('error', 'Error', "You don't have permission to edit");
                        }
                    }, function () {
                        toaster.pop('error', 'Error', 'Something went wrong! We fix this ASAP');
                    });
            }

            function deleteNoteHistory(note) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function (result) {
                    medicationService.deleteNote(note)
                        .then(function (data) {
                            if (data.success) {
                                var index = $scope.medicationNoteHistory.indexOf(note);
                                $scope.medicationNoteHistory.splice(index, 1);
                                toaster.pop('success', 'Done', 'Deleted note successfully');
                            } else {
                                toaster.pop('error', 'Error', "You don't have permission to delete");
                            }
                        }, function () {
                            toaster.pop('error', 'Error', 'Something went wrong! We fix this ASAP');
                        });
                }, function () {
                    return false;
                });
            }
        });
    /* End of controller */
})();