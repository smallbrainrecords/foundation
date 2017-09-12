(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('IndividualDataCtrl', IndividualDataCtrl);
    IndividualDataCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'problemService', 'sharedService', 'toaster', '$location', 'dataService', 'patientService'];

    function IndividualDataCtrl($scope, $routeParams, ngDialog, problemService, sharedService, toaster, $location, dataService, patientService) {
        // $scope.patient_id = $('#patient_id').val();
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

            // patientService.fetchActiveUser().then(function (data) {
            //     $scope.active_user = data['user_profile'];
            // });

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
                $scope.editForm.time = moment().format("HH:mm");
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
    }
})();