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
        .controller('DataSettingsCtrl', DataSettingsCtrl);
    DataSettingsCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'problemService', 'toaster', 'sharedService', '$location', 'dataService', 'patientService']

    function DataSettingsCtrl($scope, $routeParams, ngDialog, problemService, toaster, sharedService, $location, dataService, patientService) {

        $scope.data_id = $routeParams.data_id;
        $scope.show_edit_data = false;

        $scope.toggleEdit = toggleEdit;
        $scope.saveEdit = saveEdit;
        $scope.deleteData = deleteData;
        $scope.change_graph_type = change_graph_type;

        init();

        function init() {
            dataService.fetchDataInfo($scope.data_id).then(function (data) {
                $scope.data = data['info'];
            });
        }

        function toggleEdit() {
            $scope.show_edit_data = !$scope.show_edit_data;
        }

        function saveEdit(data) {
            let form = {};
            form.name = data.name;
            form.code = data.new_code;
            form.unit = data.new_unit;
            form.color = data.color;
            form.patient_id = $scope.patient_id;
            form.data_id = $scope.data_id;
            dataService.saveDataType(form).then(function (data) {
                if (data['success']) {
                    toaster.pop('success', "Done", "Saved Data Type successfully!");
                    $scope.show_edit_data = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });
        }

        function deleteData() {
            dataService.deleteData($scope.patient_id, $scope.data_id)
                .then(function (data) {
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Deleted data!');
                        $location.url('/');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    }
                }, (error) => {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });
        }

        function change_graph_type() {
            let form = {};
            form.patient_id = $scope.patient_id;
            form.data_id = $scope.data.id;
            form.graph_type = $scope.data.graph;

            dataService.updateGraphType(form).then(function (data) {
                if (data['success']) {
                    toaster.pop('success', 'Done', 'Graph type ');
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                }
            }, (error) => {
                toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');

            })
        }
    }
})();