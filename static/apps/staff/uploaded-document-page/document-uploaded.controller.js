/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('UploadedDocumentsPageCtrl', UploadedDocumentsPageCtrl);
    UploadedDocumentsPageCtrl.$inject = ["$scope", "documentService"];

    function UploadedDocumentsPageCtrl($scope, documentService) {
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

            documentService.getUploadedDocument(form).then(function (response) {
                let data = response.data;
                $scope.documents = data.documents;
                $scope.totalItems = data.total;
            });
        }
    }
})();