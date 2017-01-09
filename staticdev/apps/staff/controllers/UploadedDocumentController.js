(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('UploadedDocumentsPageCtrl', UploadedDocumentsPageCtrl);
    UploadedDocumentsPageCtrl.$inject = ["$scope", "Upload", "documentService"];

    function UploadedDocumentsPageCtrl($scope, Upload, documentService) {
        // Properties definition
        $scope.user_id = $('#user_id').val();
        $scope.documents = [];
        $scope.currentPage = 1;
        $scope.totalItems = 0;
        $scope.init = init;
        $scope.pageChanged = pageChanged;
        $scope.prevPage = prevPage;
        $scope.gotoPage = gotoPage;

        // Init data
        $scope.init();

        // Function definition
        function init(page) {
            if (page == undefined)
                page = 1;

            documentService.getUploadedDocument(page).then(function (resp) {
                $scope.documents = resp.data.documents;
                $scope.totalItems = resp.data.total;
            });
        }

        function pageChanged() {
            documentService.getUploadedDocument($scope.currentPage).then(function (resp) {
                $scope.documents = resp.data.documents;
                $scope.totalItems = resp.data.total;
            });
        }

        function prevPage() {

        }

        function gotoPage() {

        }
    }
})();