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
        .controller('AddDataCtrl', AddDataCtrl);
    AddDataCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'problemService', 'toaster', 'sharedService', '$location', 'dataService', 'patientService'];

    function AddDataCtrl($scope, $routeParams, ngDialog, problemService, toaster, sharedService, $location, dataService, patientService) {
        $scope.data_id = $routeParams.data_id;
        $scope.new_data = {};
        $scope.new_data.date = moment().format("MM/DD/YYYY");
        $scope.new_data.time = moment().format("HH:mm");

        $scope.add_data = add_data;

        init();

        function init() {
            dataService.fetchDataInfo($scope.data_id).then(function (data) {
                $scope.data = data['info'];
            });
        }

        function add_data(new_data) {
            if (new_data.time == "" || new_data.time == undefined) {
                new_data.time = moment().format("HH:mm");
            }
            if (!moment(new_data.time, "HH:mm").isValid()) {
                toaster.pop('error', 'Error', 'Please enter time!');
                return;
            }
            new_data.datetime = new_data.date + " " + new_data.time;

            angular.forEach($scope.data.observation_components, function (component, key) {
                new_data.value = component.new_value;
                dataService.addData($scope.patient_id, component.id, new_data).then(function (data) {
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Added data!');
                        if (key == $scope.data.observation_components.length - 1)
                            $location.url('/data/' + $scope.data_id);
                    } else {
                        toaster.pop('error', 'Error', 'Invalid entered data format!');
                    }
                }, () => {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });
            });
        }
    }
})();