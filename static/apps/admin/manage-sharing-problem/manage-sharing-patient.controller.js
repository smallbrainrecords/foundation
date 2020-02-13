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
    angular.module('AdminApp')
        .controller('ManageSharingProblemCtrl', function ($scope, $routeParams, ngDialog,
                                                          adminService, $location, $anchorScroll, toaster) {
            $scope.patient_id = $routeParams['patientId'];
            $scope.sharing_patient_id = $routeParams.sharing_patient_id;
            $scope.inArray = inArray;
            $scope.changeSharingProblem = changeSharingProblem;
            init();

            function init() {
                adminService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });
                adminService.getUserInfo($scope.patient_id).then(function (data) {
                    $scope.shared_patient = data['user_profile'];
                });
                adminService.getUserInfo($scope.sharing_patient_id).then(function (data) {
                    $scope.sharing_patient = data['user_profile'];
                });
                adminService.fetchProblems($scope.patient_id).then(function (data) {
                    $scope.problems = data['problems'];
                });
                adminService.fetchSharingProblems($scope.patient_id, $scope.sharing_patient_id).then(function (data) {
                    $scope.sharing_problems = data['sharing_problems'];
                });
            }

            function inArray(array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value.id == item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            }

            function changeSharingProblem(problem) {
                var is_existed = false;
                var index;
                angular.forEach($scope.sharing_problems, function (value, key2) {
                    if (value.id == problem.id) {
                        is_existed = true;
                        index = key2;
                    }
                });
                if (is_existed) {
                    $scope.sharing_problems.splice(index, 1);
                    adminService.removeSharingProblems($scope.patient_id, $scope.sharing_patient_id, problem.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Removed problem');
                    });
                } else {
                    $scope.sharing_problems.push(problem);
                    adminService.addSharingProblems($scope.patient_id, $scope.sharing_patient_id, problem.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Added problem');
                    });
                }
            }
        });
    /* End of controller */
})();