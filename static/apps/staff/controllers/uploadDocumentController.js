(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('UploadDocumentsCtrl', UploadDocumentsCtrl);
    UploadDocumentsCtrl.$inject = ["$scope", "Upload", "documentService"];

    function UploadDocumentsCtrl($scope, Upload, documentService) {
        // Properties definition

        // Current logged in user
        $scope.user_id = $('#user_id').val();
        $scope.uploadFile = documentService.uploadDocument;
        $scope.logs = [];

        // Listeners
        $scope.$watch('files', function () {
            $scope.uploadFile($scope.files, $scope.logs, $scope.user_id);
        });
    }
})();