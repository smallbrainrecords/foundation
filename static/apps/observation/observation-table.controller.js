(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('ObservationTableCtrl', ObservationTableCtrl);
    ObservationTableCtrl.$inject = ['$scope', 'patientService'];

    function ObservationTableCtrl($scope, patientService) {
        $scope.last5Days = [moment().subtract(4, 'd').format('x'), moment().subtract(3, 'd').format('x'), moment().subtract(2, 'd').format('x'), moment().subtract(1, 'd').format('x'), moment().format('x')];

        init();

        function init() {
            patientService.getVitalTableViews($scope.patient_id).then((response) => {
                if (response.data.success) {
                    $scope.vitals = response.data.vitals;
                }
            });
        }
    }
})();