(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('MedicationCtrl', function ($scope, $routeParams, ngDialog, problemService, toaster, $location, patientService, $filter, inrService, prompt) {

            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.medication_id = $routeParams.medication_id;
            
            patientService.fetchActiveUser().then(function (data) {
                $scope.active_user = data['user_profile'];
            });

            inrService.fetchMedicationInfo($scope.patient_id, $scope.medication_id).then(function (data) {
                $scope.medication = data['info'];
            });

            $scope.dosage_increase = function() {
                if ($scope.medication.concept_id == null) {
                    prompt({
                        "message": "This is largest dosage form"
                    }).then(function(result){
                        return false;
                    },function(){
                        return false;
                    });
                }
            };

            $scope.dosage_decrease = function() {
                if ($scope.medication.concept_id == null) {
                    prompt({
                        "message": "This is smallest dosage form"
                    }).then(function(result){
                        return false;
                    },function(){
                        return false;
                    });
                }
            };

            $scope.see_medication_history = function() {
                $scope.medication.show_medication_history = !$scope.medication.show_medication_history;
            };

            $scope.add_note = function(form, oldNote) {
                if (form.note == '') return;
                form.medication_id = $scope.medication.id;
                form.patient_id = $scope.patient_id;
                inrService.addMedicationNote(form).then(function(data) {
                    $scope.medication.medication_notes.push(data['note']);
                    if (typeof oldNote !== 'undefined')
                        form.note = oldNote;
                    toaster.pop('success', 'Done', 'Added note!');
                });
            };

            $scope.edit_note = function(note) {
                note.show_edit_note = !note.show_edit_note;
            };

            $scope.save_note = function(note) {
                inrService.editNote(note).then(function(data) {
                    note.show_edit_note = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            };

            $scope.delete_note = function(note) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function(result){
                    inrService.deleteNote(note).then(function(data){
                        var index = $scope.medication.medication_notes.indexOf(note);
                        $scope.medication.medication_notes.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted note successfully');
                    });
                },function(){
                    return false;
                });
            };


            // pin to problem
            problemService.fetchProblems($scope.patient_id).then(function (data) {
                $scope.problems = data['problems'];

                inrService.fetchPinToProblem($scope.medication_id).then(function (data) {
                    $scope.pins = data['pins'];

                    angular.forEach($scope.problems, function (problem) {
                        if ($scope.isInPins($scope.pins, problem)) {
                            problem.pin = true;
                        }
                    });
                });
            });

            $scope.isInPins = function (array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value.problem == item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            };

            /*
             * toggle pin to new problem, display list of current patient problems
             */
            $scope.show_pin_to_new_problem = false;
            $scope.toggle_pin_to_new_problem = function () {
                $scope.show_pin_to_new_problem = !$scope.show_pin_to_new_problem;
            };

            $scope.medication_pin_to_problem = function (medication_id, problem_id) {
                var form = {};
                form.medication_id = medication_id;
                form.problem_id = problem_id;

                inrService.medicationPinToProblem($scope.patient_id, form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Pinned problem!');
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            };

            $scope.open_problem = function (problem) {
                $location.path('/problem/' + problem.id);
            };

        });
    /* End of controller */
})();