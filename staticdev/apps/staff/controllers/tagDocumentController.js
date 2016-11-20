(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('TagDocumentCtrl', TagDocumentCtrl);

    TagDocumentCtrl.$inject = ['$scope'];

    /**
     *
     * @param $scope
     * @constructor
     */
    function TagDocumentCtrl($scope) {
        $scope.tagPage = "Tag Document Page";
    }
})();