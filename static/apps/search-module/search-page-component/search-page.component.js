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
    angular.module('app.searchModule')
        .controller('searchPageComponent', searchPageComponent);

    searchPageComponent.$inject = ['$scope', 'searchingService']

    function searchPageComponent($scope, searchingService) {
        $scope.searchIsFocused = false;
        $scope.searchIsLoading = false;
        $scope.searchQuery = "";
        $scope.patients = [];
        $scope.inactivePatients = [];
        $scope.notes = [];
        $scope.todos = [];
        $scope.goals = [];
        $scope.summaries = [];
        $scope.tabs = [];
        $scope.textComponents = [];
        $scope.documents = [];

        $scope.onFocus = onFocus;
        $scope.closeSearch = closeSearch;
        $scope.searchParamUpdated = searchParamUpdated;

        function onFocus() {
            $scope.searchQuery = "";
            $scope.searchIsFocused = true;
        }

        function searchParamUpdated() {
            if ($scope.searchQuery.length >= 3) {
                $scope.searchIsLoading = true;
                searchingService.searchPatient($scope.searchQuery, ["notes", "goals", "todos", "summaries", "tabs", "text_components", "documents"])
                    .then(response => {
                        $scope.searchIsLoading = false;
                        $scope.patients = response.data.patients;
                        $scope.inactivePatients = response.data.inactive_patients;
                        $scope.notes = response.data.notes;
                        $scope.goals = response.data.goals;
                        $scope.todos = response.data.todos;
                        $scope.summaries = response.data.summaries;
                        $scope.tabs = response.data.tabs;
                        $scope.textComponents = response.data.text_components;
                        $scope.documents = response.data.documents;
                    });
            }
        }

        function closeSearch() {
            $scope.searchQuery = "";
            $scope.searchIsFocused = false;
            $scope.searchIsLoading = false;
        }
    }
})();
