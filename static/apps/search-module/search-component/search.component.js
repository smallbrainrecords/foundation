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
        .component('searchComponent', {
            templateUrl: "/static/apps/search-module/search-component/search.template.html",
            controller: SearchComponentCtrl,
        });

    SearchComponentCtrl.$inject = ['searchingService']

    /***
     *
     * @param searchingService
     * @constructor
     */
    function SearchComponentCtrl(searchingService) {
        let ctrl = this;
        ctrl.searchQuery = "";
        ctrl.patients = [];
        ctrl.searchIsFocused = false;

        ctrl.searchParamUpdated = searchParamUpdated;
        ctrl.onFocus = onFocus;
        ctrl.onBlurred = onBlurred;
        ctrl.exitSearch = exitSearch;


        function exitSearch() {
            ctrl.searchQuery = "";
            ctrl.patients = [];
            ctrl.searchIsFocused = false;
        }

        function onBlurred() {
            ctrl.searchIsFocused = false;
            ctrl.searchQuery = "";
            ctrl.patients = [];
        }

        function onFocus() {
            ctrl.searchIsFocused = true;
        }

        function searchParamUpdated() {
            if (ctrl.searchQuery.length >= 3)
                searchingService.searchPatient(ctrl.searchQuery)
                    .then(response => {
                        ctrl.patients = response.data.patients;
                    });
        }
    }
})();
