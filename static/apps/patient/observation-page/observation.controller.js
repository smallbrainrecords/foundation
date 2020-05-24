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
        .controller('DataCtrl', DataCtrl);
    DataCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'problemService', 'toaster', '$location', 'sharedService', 'dataService', 'patientService', '$filter'];

    function DataCtrl($scope, $routeParams, ngDialog, problemService, toaster, $location, sharedService, dataService, patientService, $filter) {

        $scope.data_id = $routeParams.data_id;
        $scope.viewMode = 'Year';
        $scope.show_pin_to_new_problem = false;
        $scope.quickEntryDataObj = {
            date: moment().format("MM/DD/YYYY"),
            time: moment().format("HH:mm"),
            datetime: moment().format("MM/DD/YYYY HH:mm")
        };

        $scope.isInPins = isInPins;
        $scope.toggle_pin_to_new_problem = toggle_pin_to_new_problem;
        $scope.data_pin_to_problem = data_pin_to_problem;
        $scope.open_problem = open_problem;
        $scope.quickAddDataPoint = quickAddDataPoint;

        init();


        function init() {
            $scope.$watch("viewMode", function (newVal, oldVal) {
                if (newVal !== oldVal) {
                    refreshGraph();
                }
            });

            dataService.fetchDataInfo($scope.data_id).then(function (response) {
                let data = response.data;
                $scope.data = data['info'];

                // Default data chart
                if ($scope.data.graph == null)
                    $scope.data.graph = 'Line';
                refreshGraph();
            });

            problemService.fetchProblems($scope.patient_id).then(function (response) {
                let data = response.data;
                $scope.problems = data['problems'];

                dataService.fetchPinToProblem($scope.data_id).then(function (response) {
                    let data = response.data;
                    $scope.pins = data['pins'];

                    angular.forEach($scope.problems, function (problem) {
                        if ($scope.isInPins($scope.pins, problem)) {
                            problem.pin = true;
                        }
                    });
                });
            });
        }

        /**
         * Regenerate graph
         */
        function refreshGraph() {
            // Temporary data using for generate graph
            let tmpData = angular.copy($scope.data);

            // Sorting before processing
            _.map(tmpData.observation_components, function (item, key) {
                item.observation_component_values = dataService.updateViewMode($scope.viewMode, item.observation_component_values);

                // Sorting before generating
                item.observation_component_values = $filter('orderBy')(item.observation_component_values, "effective_datetime");
            });
            $scope.data.chartData = dataService.generateChartData(tmpData);
            $scope.data.chartLabel = dataService.generateChartLabel(tmpData);

            // Unaffected graph option when timerange filter changed
            $scope.data.chartSeries = dataService.generateChartSeries(tmpData);
            $scope.data.mostRecentValue = dataService.generateMostRecentValue(tmpData);
        }

        function isInPins(array, item) {
            let is_existed = false;
            angular.forEach(array, function (value, key2) {
                if (value.problem === item.id) {
                    is_existed = true;
                }
            });
            return is_existed;
        }

        function toggle_pin_to_new_problem() {
            $scope.show_pin_to_new_problem = !$scope.show_pin_to_new_problem;
        }

        function data_pin_to_problem(index, data_id, problem_id) {
            var form = {};
            form.data_id = data_id;
            form.problem_id = problem_id;
            dataService.dataPinToProblem($scope.patient_id, form).then(function (response) {
                let data = response.data;
                if (data['success']) {
                    toaster.pop('success', 'Done', 'Pinned problem!');
                } else if (!data['success']) {
                    toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                } else if (data['success'] === "notallow") {
                    toaster.pop('error', 'Error', 'You can\'t  unpin this data!');
                    $scope.problems[index].pin = true;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });
        }

        function open_problem(problem) {
            $location.path('/problem/' + problem.id);
        }

        function quickAddDataPoint(quickEntryDataObj) {
            angular.forEach($scope.data.observation_components, function (component, key) {
                quickEntryDataObj.value = component.new_value;
                dataService.addData($scope.patient_id, component.id, quickEntryDataObj)
                    .then(function (response) {
                        let data = response.data;
                        if (data['success']) {
                            toaster.pop('success', 'Done', 'Added data!');
                            // Empty entered data
                            component.new_value = "";

                            // Push it to data
                            component.observation_component_values.push(data.value);

                            // Refresh graph
                            refreshGraph();
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                        }
                    }, () => {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    });
            });
        }

    }
})();