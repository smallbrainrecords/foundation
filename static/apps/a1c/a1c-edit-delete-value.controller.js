(function () {
    'use strict';
    angular.module('ManagerApp')

    /**
     * This should be named to value listing page
     */
        .controller('EditOrDeleteValuesCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                        sharedService, toaster, patientService, prompt) {

            $scope.a1c_id = $routeParams.a1c_id;

            $scope.deleteValue = deleteValue;

            init();

            function init() {
                a1cService.fetchA1cInfo($scope.a1c_id).then(function (data) {
                    $scope.a1c = data['info'];

                    if ($scope.a1c.observation.observation_components.length > 0)
                        $scope.first_component = $scope.a1c.observation.observation_components[0];
                });
            }

            function deleteValue(value) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a value is forever. There is no undo."
                }).then(function (result) {
                    a1cService.deleteValue(value).then(function (data) {
                        let index = $scope.first_component.observation_component_values.indexOf(value);
                        $scope.first_component.observation_component_values.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted value successfully');
                    });
                }, function () {
                    return false;
                });
            }
        })
})();