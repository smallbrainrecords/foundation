(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('UploadedDocumentsPageCtrl', UploadedDocumentsPageCtrl);
    UploadedDocumentsPageCtrl.$inject = ["$scope", "documentService"];

    function UploadedDocumentsPageCtrl($scope, documentService) {
        // Properties definition
        $scope.user_id = $('#user_id').val();
        $scope.documents = [];
        $scope.currentPage = 1;
        $scope.itemPerPage = 10;
        $scope.totalItems = 0;
        $scope.showPinned = false;

        $scope.togglePinnedDocument = togglePinnedDocument;
        $scope.updateSearchTerm = updateSearchTerm;

        init();

        function init() {
            $scope.updateSearchTerm();
        }

        function togglePinnedDocument() {
            $scope.showPinned = !$scope.showPinned;

            $scope.updateSearchTerm();
        }

        function updateSearchTerm() {
            var form = {
                page: $scope.currentPage,
                show_pinned: $scope.showPinned
            };

            documentService.getUploadedDocument(form).then(function (resp) {
                $scope.documents = resp.data.documents;
                $scope.totalItems = resp.data.total;
            });
        }
    }
})();