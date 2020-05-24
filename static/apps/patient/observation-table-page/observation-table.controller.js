(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('ObservationTableCtrl', ObservationTableCtrl);
    ObservationTableCtrl.$inject = ['$scope', 'patientService'];

    function ObservationTableCtrl($scope, patientService) {

        init();

        function init() {
            patientService.getVitalTableViews($scope.patient_id).then((response) => {
                let data = response.data;
                if (data.success) {
                    $scope.vitals = data.vitals;
                }
            });
        }
    }
})();