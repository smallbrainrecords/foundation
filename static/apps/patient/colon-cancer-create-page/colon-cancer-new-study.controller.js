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

    angular.module('ManagerApp')
        .controller('AddNewStudyCtrl', AddNewStudyCtrl);

    AddNewStudyCtrl.$inject = ['$scope', '$routeParams', 'DATE_CONFIG', 'toaster', '$location', 'sharedService', 'colonService', 'COLON_FINDING'];

    function AddNewStudyCtrl($scope, $routeParams, DATE_CONFIG, toaster, $location, sharedService, colonService, COLON_FINDING) {

        // Properties
        $scope.findingSet = COLON_FINDING;
        $scope.dateConfig = DATE_CONFIG;
        $scope.isOpened = false;
        $scope.colonCancerStudyFormModel = {
            finding: "",
            result: "",
            date: new Date(),
            note: "",
        };

        // Behaviors
        $scope.addStudy = addStudy;

        init();

        function init() {
            // TODO: To be improved
            colonService.fetchColonCancerInfo($routeParams.colonId).then(function (data) {
                $scope.colon_cancer = data['info'];
            });
        }

        function addStudy(study) {
            if ($scope.colonCancerForm.$invalid) return;

            let colonCancerStudyDataModel = {
                finding: $scope.colonCancerStudyFormModel.finding.label,
                result: $scope.colonCancerStudyFormModel.result,
                date: $scope.colonCancerStudyFormModel.date.toISOString(),
                note: $scope.colonCancerStudyFormModel.note,
            };

            colonService.addNewStudy($routeParams.colonId, colonCancerStudyDataModel)
                .then((data) => {
                    if (data.success)
                        toaster.pop('success', 'Done', 'Saved study!');
                });
        }
    }
})();