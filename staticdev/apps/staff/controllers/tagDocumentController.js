(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('TagDocumentCtrl', TagDocumentCtrl);

    TagDocumentCtrl.$inject = ['$scope', 'documentService', '$routeParams'];

    /**
     *
     * @param $scope
     * @param documentService
     * @param $routeParams
     * @constructor
     */
    function TagDocumentCtrl($scope, documentService, $routeParams) {

        documentService.getDocumentInfo($routeParams.documentId).then(function (resp) {
            $scope.document = resp.data.info;
        });

        $scope.pinDocument2Patient = pinDocument2Patient;
        $scope.pinDocument2Todo = documentService.pinDocument2Todo;
        $scope.pinDocument2Problem = documentService.pinDocument2Problem;
        function pinDocument2Patient() {
            //TODO Implement details here
        }
    }
})();