(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('ShowAllDataCtrl', ShowAllDataCtrl);
    ShowAllDataCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'problemService', 'sharedService', 'toaster', '$location', 'dataService'];

    function ShowAllDataCtrl($scope, $routeParams, ngDialog, problemService, sharedService, toaster, $location, dataService) {
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
    }
})();