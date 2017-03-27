(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('DataCtrl', function ($scope, $routeParams, ngDialog, problemService, toaster, $location, sharedService, dataService, patientService, $filter) {

            $scope.patient_id = $('#patient_id').val();
            $scope.data_id = $routeParams.data_id;
            $scope.viewMode = 'Year';
            $scope.show_pin_to_new_problem = false;

            $scope.isInPins = isInPins;
            $scope.toggle_pin_to_new_problem = toggle_pin_to_new_problem;
            $scope.data_pin_to_problem = data_pin_to_problem;
            $scope.open_problem = open_problem;

            init();

            function init() {
                $scope.$watch("viewMode", function (newVal, oldVal) {
                    if (newVal != oldVal) {
                        // Temporary data using for generate graph
                        var tmpData = angular.copy($scope.data);

                        // Sorting before processing
                        _.map(tmpData.observation_components, function (item, key) {
                            item.observation_component_values = dataService.updateViewMode($scope.viewMode, item.observation_component_values);

                            // Sorting before generating
                            item.observation_component_values = $filter('orderBy')(item.observation_component_values, "effective_datetime");
                        });
                        $scope.data.chartData = dataService.generateChartData(tmpData);
                        $scope.data.chartLabel = dataService.generateChartLabel(tmpData);
                    }
                });

                patientService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];

                });

                dataService.fetchDataInfo($scope.data_id).then(function (data) {
                    $scope.data = data['info'];

                    // Default data chart
                    if ($scope.data.graph == null || $scope.data.graph == undefined)
                        $scope.data.graph = 'Line';

                    // Temporary data using for generate graph
                    var tmpData = angular.copy($scope.data);

                    // Sorting before processing
                    _.map(tmpData.observation_components, function (item, key) {
                        item.observation_component_values = dataService.updateViewMode($scope.viewMode, item.observation_component_values);

                        // Sorting before generating
                        item.observation_component_values = $filter('orderBy')(item.observation_component_values, "effective_datetime");
                    });
                    $scope.data.chartData = dataService.generateChartData(tmpData);
                    $scope.data.chartLabel = dataService.generateChartLabel(tmpData);

                    // Unaffected graph option when timerang filter changed
                    $scope.data.chartSeries = dataService.generateChartSeries(tmpData);
                    $scope.data.mostRecentValue = dataService.generateMostRecentValue(tmpData);
                });

                problemService.fetchProblems($scope.patient_id).then(function (data) {
                    $scope.problems = data['problems'];

                    dataService.fetchPinToProblem($scope.data_id).then(function (data) {
                        $scope.pins = data['pins'];

                        angular.forEach($scope.problems, function (problem) {
                            if ($scope.isInPins($scope.pins, problem)) {
                                problem.pin = true;
                            }
                        });
                    });
                });
            }

            function isInPins(array, item) {
                let is_existed = false;
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

            function data_pin_to_problem(index, data_id, problem_id) {
                var form = {};
                form.data_id = data_id;
                form.problem_id = problem_id;
                dataService.dataPinToProblem($scope.patient_id, form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Pinned problem!');
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    } else if (data['success'] == "notallow") {
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
        })
        .controller('AddDataCtrl', function ($scope, $routeParams, ngDialog, problemService, toaster, sharedService, $location, dataService, patientService) {
            $scope.patient_id = $('#patient_id').val();
            $scope.data_id = $routeParams.data_id;
            $scope.new_data = {};
            $scope.new_data.date = moment().format("MM/DD/YYYY");
            $scope.add_data = add_data;

            init();

            function init() {

                patientService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];

                });

                dataService.fetchDataInfo($scope.data_id).then(function (data) {
                    $scope.data = data['info'];
                });
            }

            function add_data(new_data) {
                if (new_data.time == "" || new_data.time == undefined) {
                    new_data.time = "12:00";
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
                            toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                        }
                    }, () => {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    });
                });
            }
        })
        .controller('ShowAllDataCtrl', function ($scope, $routeParams, ngDialog, problemService, sharedService, toaster, $location, dataService) {
            $scope.data = [];
            $scope.displayedComponent = [];
            $scope.editLink = [];

            init();

            function init() {
                dataService.fetchDataInfo($routeParams.data_id)
                    .then(function (data) {
                        $scope.data = data['info'];

                        // Generate observation label for which one having more than 1 component (ex: component_one_name/component_two_name/component_three_name)
                        let tmpData = angular.copy($scope.data);
                        if (tmpData.observation_components.length > 1) {
                            $scope.componentLabel = _.map(tmpData.observation_components, item => item.name).join('/');
                        }

                        // Rotate multi component values & also generate edit link  which is easier for data displaying(ex [[1,2,3,4],[1,2,3,4]] -> [[1,1],[2,2],[3,3],[4,4]])
                        let componentArr = _.pluck(tmpData.observation_components, 'observation_component_values');
                        $scope.displayedComponent = _.zip(...componentArr);
                        $scope.editLink = _.map($scope.displayedComponent, (value, idx) => _.pluck(value, 'id').join('&'))
                    });
            }
        })
        .controller('IndividualDataCtrl', function ($scope, $routeParams, ngDialog, problemService, sharedService, toaster, $location, dataService, patientService) {
            $scope.patient_id = $('#patient_id').val();
            // List of all observation component value pair is requested for editing
            $scope.dataID = $routeParams.dataId;
            $scope.componentValueIds = $routeParams.componentValueIds.split('&');
            $scope.show_edit = false;
            $scope.editComponentValue = [];
            $scope.editForm = {};

            $scope.deleteData = deleteData;
            $scope.editFinished = editFinished;
            $scope.save_data = saveData;
            $scope.toggleEdit = toggleEdit;

            init();

            function init() {

                patientService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });

                dataService.fetchDataInfo($scope.dataID).then(function (data) {
                    $scope.data = data['info'];

                    // Rotate multi component values & also generate edit link  which is easier for data displaying(ex [[1,2,3,4],[1,2,3,4]] -> [[1,1],[2,2],[3,3],[4,4]])
                    // Get component value pair used for editing
                    let componentArr = _.pluck($scope.data.observation_components, 'observation_component_values');
                    $scope.displayedComponent = _.zip(...componentArr);
                    let item = _.map($scope.componentValueIds, value => parseInt(value));
                    $scope.editComponentValue = _.find($scope.displayedComponent, (value, idx) => {
                        if (_.isEqual(item, _.pluck(value, 'id')))
                            return value;
                    });

                    // TODO: Performance enhancement.
                    _.map($scope.editComponentValue, (componentValue, componentValueIndex) => {
                        _.map($scope.data.observation_components, (component, componentIndex) => {
                            if (componentValue.component === component.id)
                                component.new_value = componentValue.value_quantity
                        });
                        $scope.editForm.date = componentValue.date;
                        $scope.editForm.time = componentValue.time;
                    });
                });
            }

            function toggleEdit() {
                $scope.show_edit = !$scope.show_edit;
            }


            function deleteData() {
                dataService.deleteComponentValues($scope.patient_id, $scope.componentValueIds)
                    .then(function (response) {
                        if (response.data['success']) {
                            toaster.pop('success', 'Done', 'Deleted data!');
                            $location.url('/data/' + $scope.data.id + '/show_all_data');
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                        }
                    }, (error) => {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    });
            }

            function editFinished(componentValueIndex, data) {
                $scope.show_edit = false;

                $scope.editComponentValue[componentValueIndex] = data;
            }

            function saveData() {
                if (_.isEmpty($scope.editForm.time) || _.isUndefined($scope.editForm.time)) {
                    $scope.editForm.time = "12:00";
                }
                if (!moment($scope.editForm.time, "HH:mm").isValid()) {
                    toaster.pop('error', 'Error', 'Please enter time!');
                    return;
                }
                $scope.editForm.datetime = $scope.editForm.date + " " + $scope.editForm.time;
                _.map($scope.editComponentValue, (value, index) => {
                    $scope.editForm.value_quantity = _.findWhere($scope.data.observation_components, {id: value.component}).new_value;
                    dataService.saveData($scope.patient_id, value.id, $scope.editForm).then(function (data) {
                        if (data['success']) {
                            toaster.pop('success', 'Done', 'Saved data!');
                            $scope.editFinished(index, data.info);
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                        }
                    }, () => {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    });
                });
            }
        })
        .controller('DataSettingsCtrl', function ($scope, $routeParams, ngDialog, problemService, toaster, sharedService, $location, dataService, patientService) {

            $scope.patient_id = $('#patient_id').val();
            $scope.data_id = $routeParams.data_id;
            $scope.show_edit_data = false;

            $scope.toggleEdit = toggleEdit;
            $scope.saveEdit = saveEdit;
            $scope.deleteData = deleteData;
            $scope.change_graph_type = change_graph_type;

            init();

            function init() {
                patientService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });

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
        });
})();