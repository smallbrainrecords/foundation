(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('DataSettingsCtrl', DataSettingsCtrl);
    DataSettingsCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'problemService', 'toaster', 'sharedService', '$location', 'dataService', 'patientService']

    function DataSettingsCtrl($scope, $routeParams, ngDialog, problemService, toaster, sharedService, $location, dataService, patientService) {

        // $scope.patient_id = $('#patient_id').val();
        $scope.data_id = $routeParams.data_id;
        $scope.show_edit_data = false;

        $scope.toggleEdit = toggleEdit;
        $scope.saveEdit = saveEdit;
        $scope.deleteData = deleteData;
        $scope.change_graph_type = change_graph_type;

        init();

        function init() {
            // patientService.fetchActiveUser().then(function (data) {
            //     $scope.active_user = data['user_profile'];
            // });

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