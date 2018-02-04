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
        .controller('EditValueCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                               sharedService, toaster, patientService, prompt, $location) {


            $scope.value_id = $routeParams.value_id;

            $scope.deleteValue = deleteValue;
            $scope.editValue = editValue;
            $scope.add_note = add_note;
            $scope.toggleEditNote = toggleEditNote;
            $scope.toggleSaveNote = toggleSaveNote;
            $scope.deleteNote = deleteNote;

            init();

            function init() {

                a1cService.fetchObservationValueInfo($scope.value_id).then(function (data) {
                    $scope.value = data['info'];
                    $scope.a1c_id = data['a1c_id'];
                    $scope.today = moment();
                    $scope.a1c_date = moment($scope.value.effective_datetime);
                    $scope.a1c_date_format = moment($scope.value.effective_datetime).format("YYYY-MM-DD");
                });
            }

            function deleteValue(value) {
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
            }

            function editValue(value_id, value_quantity, effective_datetime) {
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

            function add_note(form) {
                if (form.note == '') return;
                form.value_id = $scope.value_id;
                a1cService.addValueNote(form).then(function (data) {
                    $scope.value.observation_value_notes.push(data['note']);
                    form.note = '';
                    toaster.pop('success', 'Done', 'Added Note!');
                });
            }

            function toggleEditNote(note) {
                note.edit = true;
            }

            function toggleSaveNote(note) {
                a1cService.editValueNote(note).then(function (data) {
                    note.edit = false;
                    toaster.pop('success', 'Done', 'Edited note successfully');
                });
            }

            function deleteNote(note) {
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
})();