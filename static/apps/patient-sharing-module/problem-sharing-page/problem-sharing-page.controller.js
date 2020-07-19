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
    angular.module('app.patientSharingModule')
        .controller('ProblemSharingCtrl', ProblemSharingCtrl);
    ProblemSharingCtrl.$inject = ['$scope', '$routeParams', 'adminService', 'toaster'];

    function ProblemSharingCtrl($scope, $routeParams, adminService, toaster) {
        $scope.patientId = $routeParams.patientId;
        $scope.sharingPatientId = $routeParams.sharingPatientId;

        $scope.sharingPatient = {};
        $scope.sharedPatient = {};
        $scope.problems = [];
        $scope.sharingProblems = [];

        $scope.isShared = isShared;
        $scope.changeSharingProblem = changeSharingProblem;

        init();

        function init() {
            adminService.getUserInfo($scope.patientId)
                .then((response) => {
                    let data = response.data;
                    $scope.sharingPatient = data['user_profile'];
                });

            adminService.getUserInfo($scope.sharingPatientId)
                .then((response) => {
                    let data = response.data;
                    $scope.sharedPatient = data['user_profile'];
                });

            adminService.fetchProblems($scope.patientId)
                .then((response) => {
                    let data = response.data;
                    $scope.problems = data['problems'];
                });

            adminService.fetchSharingProblems($scope.patientId, $scope.sharingPatientId)
                .then((response) => {
                    let data = response.data;
                    $scope.sharingProblems = data['sharing_problems'];
                });
        }

        function isShared(array, item) {
            let is_existed = false;
            angular.forEach(array, function (value) {
                if (value.id === item.id) {
                    is_existed = true;
                }
            });
            return is_existed;
        }

        function changeSharingProblem(problem) {
            let is_existed = false;
            let index;
            angular.forEach($scope.sharingProblems, function (value, key2) {
                if (value.id === problem.id) {
                    is_existed = true;
                    index = key2;
                }
            });
            if (is_existed) {
                $scope.sharingProblems.splice(index, 1);
                adminService.removeSharingProblems($scope.patientId, $scope.sharingPatientId, problem.id)
                    .then((response) => {
                        let data = response.data;
                        toaster.pop('success', 'Done', 'Removed problem');
                    });
            } else {
                $scope.sharingProblems.push(problem);
                adminService.addSharingProblems($scope.patientId, $scope.sharingPatientId, problem.id)
                    .then((response) => {
                        let data = response.data;
                        toaster.pop('success', 'Done', 'Added problem');
                    });
            }
        }
    }
})();