/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('MedicationCtrl', function ($scope, $routeParams, $filter, $location, prompt, toaster,
                                                sharedService, patientService, problemService, medicationService) {

            // States
            $scope.medicationId = $routeParams.medication_id;
            $scope.showMedicationSearch = false;
            $scope.showMedicationHistory = false;
            $scope.showPinToNewProblem = false;
            $scope.medicationHistory = [];
            $scope.medicationNoteHistory = [];
            $scope.encounters = [];

            // Behaviors
            $scope.toggleMedicationHistory = toggleMedicationHistory;
            $scope.toggleMedicationSearch = toggleMedicationSearch;
            $scope.togglePinToNewProblem = togglePinToNewProblem;
            $scope.addNote = addNote;
            $scope.isInPins = isInPins;
            $scope.medicationPinToProblem = medicationPinToProblem;
            $scope.openProblem = openProblem;
            $scope.changeActiveMedication = changeActiveMedication;
            $scope.changeDosage = changeDosage;
            $scope.updateNoteHistory = updateNoteHistory;
            $scope.deleteNoteHistory = deleteNoteHistory;

            init();

            ////////////////////////

            function init() {

                medicationService.fetchMedicationInfo($scope.patient_id, $scope.medicationId).then(data => {
                    $scope.medication = data['info'];
                    $scope.medicationHistory = data['history'];
                    $scope.medicationNoteHistory = data['noteHistory'];
                });

                // pin to problem
                problemService.fetchProblems($scope.patient_id).then(data => {
                    $scope.problems = data['problems'];

                    medicationService.fetchPinToProblem($scope.medicationId).then(data => {
                        $scope.pins = data['pins'];

                        angular.forEach($scope.problems, problem => {
                            if ($scope.isInPins($scope.pins, problem)) {
                                problem.pin = true;
                            }
                        });
                    });
                });

                medicationService.getRelatedEncounters($scope.medicationId).then(response => {
                    $scope.encounters = response['encounters'];
                })
            }

            function toggleMedicationHistory() {
                $scope.showMedicationSearch = false;
                $scope.showPinToNewProblem = false;
                $scope.showMedicationHistory = !$scope.showMedicationHistory;
            }

            function togglePinToNewProblem() {
                $scope.showMedicationSearch = false;
                $scope.showMedicationHistory = false;
                $scope.showPinToNewProblem = !$scope.showPinToNewProblem;
            }

            function toggleMedicationSearch() {
                $scope.showMedicationHistory = false;
                $scope.showPinToNewProblem = false;
                $scope.showMedicationSearch = !$scope.showMedicationSearch;
            }

            function addNote(form, oldNote) {
                if (form.note === '')
                    return;

                form.medication_id = $scope.medication.id;
                form.patient_id = $scope.patient_id;

                medicationService.addMedicationNote(form)
                    .then(data => {
                        $scope.medicationNoteHistory.push(data['note']);
                        if (typeof oldNote !== 'undefined')
                            form.note = oldNote;
                        toaster.pop('success', 'Done', 'Added note!');
                    });
            }

            function isInPins(array, item) {
                var is_existed = false;
                angular.forEach(array, (value, key2) => {
                    if (value.problem === item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            }


            function medicationPinToProblem(medication_id, problem_id) {
                let form = {};
                form.medication_id = medication_id;
                form.problem_id = problem_id;

                medicationService.medicationPinToProblem($scope.patient_id, form).then(data => {
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Pinned problem!');
                    } else if (data['success']) {
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
                medicationService.changeActiveMedication($scope.patient_id, $scope.medicationId)
                    .then(response => {
                        toaster.pop('success', 'Done', 'Changed successfully!');
                    });
            }

            function changeDosage(medication) {
                medicationService.changeDosage($scope.patient_id, $scope.medication.id, medication)
                    .then(response => {
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
                    .then(data => {
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
                }).then(result => {
                    medicationService.deleteNote(note)
                        .then(data => {
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