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

                a1cService.fetchA1cInfo($scope.a1c_id).then(function (response) {
                    let data = response.data;
                    $scope.a1c = data['info'];
                });
            }

            function addValue(value) {
                if (value === undefined) {
                    toaster.pop('error', 'Error', 'Please enter float value!');
                    return false;
                }
                if (isNaN(parseFloat(value.value))) {
                    toaster.pop('error', 'Error', 'Please enter float value!');
                    return false;
                }

                if (value.date === undefined) {
                    value.date = moment().format("YYYY-MM-DD");
                }
                value.component_id = $scope.a1c.observation.observation_components[0].id;
                a1cService.addNewValue(value).then(function (response) {
                    let data = response.data;
                    toaster.pop('success', 'Done', 'Added New value!');
                    $location.url('/problem/' + $scope.a1c.problem.id);
                });
            }

            function addValueRefused(value) {
                value = {};
                if (value.date === undefined) {
                    value.date = moment().format("YYYY-MM-DD");
                }
                value.patient_refused_A1C = true;
                value.a1c_id = $scope.a1c_id;
                a1cService.addValueRefused(value).then(function (response) {
                    let data = response.data;
                    toaster.pop('success', 'Done', 'Patient refused!');
                    $location.url('/problem/' + $scope.a1c.problem.id);
                });
            }

            function add_note(form) {
                if (form.note === '') return;
                form.a1c_id = $scope.a1c_id;
                a1cService.addNote(form).then(function (response) {
                    let data = response.data;
                    $scope.a1c.a1c_notes.push(data['note']);
                    form.note = '';
                    toaster.pop('success', 'Done', 'Added Note!');
                });
            }

            function toggleEditNote(note) {
                note.edit = true;
            }

            function toggleSaveNote(note) {
                a1cService.editNote(note).then(function (response) {
                    let data = response.data;
                    note.edit = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            }

            function deleteNote(note) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a note is forever. There is no undo."
                }).then(function (result) {
                    a1cService.deleteNote(note).then(function (response) {
                        let data = response.data;
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