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

    /**
     * This should be named to value listing page
     */
        .controller('EditOrDeleteValuesCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                        sharedService, toaster, patientService, prompt) {

            $scope.a1c_id = $routeParams.a1c_id;

            $scope.deleteValue = deleteValue;

            init();

            function init() {
                a1cService.fetchA1cInfo($scope.a1c_id).then(function (data) {
                    $scope.a1c = data['info'];

                    if ($scope.a1c.observation.observation_components.length > 0)
                        $scope.first_component = $scope.a1c.observation.observation_components[0];
                });
            }

            function deleteValue(value) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a value is forever. There is no undo."
                }).then(function (result) {
                    a1cService.deleteValue(value).then(function (data) {
                        let index = $scope.first_component.observation_component_values.indexOf(value);
                        $scope.first_component.observation_component_values.splice(index, 1);
                        toaster.pop('success', 'Done', 'Deleted value successfully');
                    });
                }, function () {
                    return false;
                });
            }
        })
})();