(function () {
    'use strict';
    angular.module('ManagerApp')
        .controller('EnterNewValueCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                   sharedService, toaster, patientService, $location) {
            $scope.a1c_id = $routeParams.a1c_id;
            $scope.addValue = addValue;
            $scope.addValueRefused = addValueRefused;
            $scope.add_note = add_note;
            $scope.toggleEditNote = toggleEditNote;
            $scope.toggleSaveNote = toggleSaveNote;
            $scope.deleteNote = deleteNote;

            init();

            function init() {

                a1cService.fetchA1cInfo($scope.a1c_id).then(function (data) {
                    $scope.a1c = data['info'];
                });
            }

            function addValue(value) {
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
            }

            function addValueRefused(value) {
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
            }

            function add_note(form) {
                if (form.note == '') return;
                form.a1c_id = $scope.a1c_id;
                a1cService.addNote(form).then(function (data) {
                    $scope.a1c.a1c_notes.push(data['note']);
                    form.note = '';
                    toaster.pop('success', 'Done', 'Added Note!');
                });
            }

            function toggleEditNote(note) {
                note.edit = true;
            }

            function toggleSaveNote(note) {
                a1cService.editNote(note).then(function (data) {
                    note.edit = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            }

            function deleteNote(note) {
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
})();