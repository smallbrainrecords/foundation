(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('UploadDocumentsCtrl', UploadDocumentsCtrl);
    UploadDocumentsCtrl.$inject = ["$scope", "documentService"];

    function UploadDocumentsCtrl($scope, documentService) {
        $scope.user_id = $('#user_id').val();
        $scope.logs = [];

        init();

        function init() {
            $scope.$watch('files', function () {
                documentService.uploadDocument($scope.files, $scope.logs, $scope.user_id);
            });
        }
    }
})();