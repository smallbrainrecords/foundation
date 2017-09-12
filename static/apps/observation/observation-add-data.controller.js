(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('AddDataCtrl', AddDataCtrl);
    AddDataCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'problemService', 'toaster', 'sharedService', '$location', 'dataService', 'patientService'];

    function AddDataCtrl($scope, $routeParams, ngDialog, problemService, toaster, sharedService, $location, dataService, patientService) {
        // $scope.patient_id = $('#patient_id').val();
        $scope.data_id = $routeParams.data_id;
        $scope.new_data = {};
        $scope.new_data.date = moment().format("MM/DD/YYYY");
        $scope.add_data = add_data;

        init();

        function init() {

            // patientService.fetchActiveUser().then(function (data) {
            //     $scope.active_user = data['user_profile'];
            //
            // });

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
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    }
                }, () => {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });
            });
        }
    }
})();