(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('UploadDocumentsCtrl', UploadDocumentsCtrl);
    UploadDocumentsCtrl.$inject = ["$scope", "Upload", "documentService", "$timeout"];

    function UploadDocumentsCtrl($scope, Upload, documentService, $timeout) {
        // Properties definition
        $scope.uploadFile = documentService.uploadDocument;
        $scope.logs = [];

        // Listeners
        $scope.$watch('files', function () {
            $scope.uploadFile($scope.files, $scope.logs);
        });
    }
})();