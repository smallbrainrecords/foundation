(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('UploadDocumentsCtrl', UploadDocumentsCtrl);
    UploadDocumentsCtrl.$inject = ["$scope", "documentService"];

    function UploadDocumentsCtrl($scope, documentService) {
        init();

        function init() {
            $scope.$watch('files', function () {
                documentService.uploadDocument($scope.files, $scope.logs, $scope.user_id);
            });
        }
    }
})();