(function () {
    'use strict';
    angular.module('ManagerApp')
        .controller('ViewDocumentCtrl', ViewDocumentCtrl);

    ViewDocumentCtrl.$inject = ['$scope', 'sharedService', '$routeParams', 'problemService', '$location'];

    /**
     * WIP: Missing status return
     * @param $scope
     * @param sharedService
     * @param $routeParams
     * @param problemService
     * @param $location
     * @constructor
     */
    function ViewDocumentCtrl($scope, sharedService, $routeParams, problemService, $location) {

        sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
            $scope.document = resp.data.info;
            $scope.todos_ready = true; // Should be removed
        });

        $scope.open_problem = function (problem) {
            $location.path('/problem/' + problem.id);
        };
    }
})();