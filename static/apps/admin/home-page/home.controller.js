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
        .controller('HomeCtrl', function ($scope, $routeParams, ngDialog, adminService, sharedService) {
            $scope.refresh_pending_users = refreshPendingUsers;
            $scope.updatePendingUser = updatePendingUser;
            $scope.refreshUserList = refreshUserList;
            $scope.nextPage = nextPage;
            $scope.prevPage = prevPage;
            $scope.nextPageDisabled = nextPageDisabled;
            $scope.prevPageDisabled = prevPageDisabled;
            init();

            function init() {
                $scope.users = [];
                $scope.loadingUsers = false;
                $scope.pageNumber = 1;
                $scope.pageSize = 10;
                $scope.totalPages = 1;
                $scope.searchText = "";
                adminService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                    refreshUserList();
                    refreshPendingUsers();
                    if ($scope.active_user.role === 'physician') {
                        var form = { 'physician_id': $scope.active_user.user.id };
                        adminService.getPhysicianTeam(form).then(function (data) {
                            $scope.team = data;
                        });
                        adminService.getPhysicianPatients(form).then(function (data) {
                            $scope.patients = data;
                        });
                    }
                });
            }

            function refreshUserList() {
                let role_form = {
                    'actor_role': $scope.active_user.role,
                    'actor_id': $scope.active_user.user.id,
                    'page_number': $scope.pageNumber,
                    'page_size': $scope.pageSize,
                    'search_text': $scope.searchText
                };
                $scope.users = [];
                $scope.loadingUsers = true;
                adminService.getUsersList(role_form).then(function (data) {
                    $scope.pageNumber = data.page_number * 1;
                    $scope.pageSize = data.page_size * 1;
                    $scope.totalPages = data.total_pages * 1;
                    $scope.users = data.users;
                    $scope.loadingUsers = false;
                });
            }

            function nextPageDisabled() {
                return !($scope.pageNumber < $scope.totalPages && !$scope.loadingUsers);
            }

            function nextPage() {
                $scope.pageNumber = $scope.pageNumber < $scope.totalPages ? $scope.pageNumber + 1 : $scope.totalPages;
                refreshUserList();
            }

            function prevPageDisabled() {
                return !($scope.pageNumber > 1 && !$scope.loadingUsers);
            }

            function prevPage() {
                $scope.pageNumber = $scope.pageNumber > 1 ? $scope.pageNumber - 1 : $scope.totalPages;
                refreshUserList();
            }

            function refreshPendingUsers() {
                let role_form = {
                    'actor_role': $scope.active_user.role,
                    'actor_id': $scope.active_user.user.id,
                    'page_number': $scope.pageNumber,
                    'page_size': $scope.pageSize
                };
                adminService.getPendingRegistrationUsersList(role_form).then(function (data) {
                    $scope.pending_users = data;
                });
            }

            function updatePendingUser(user, status) {
                switch (status) {
                    case 1: // Approve
                        if (user.role === 'patient') {
                            sharedService.approveUser(user).then(userUpdateSucceed);
                        } else {
                            alert("Please assign role!");
                        }
                        break;
                    case 0: // Reject
                        sharedService.rejectUser(user).then(userUpdateSucceed);
                        break;
                    default:
                        break;
                }

                function userUpdateSucceed() {
                    let index = $scope.pending_users.indexOf(user);
                    if (index > -1) {
                        $scope.pending_users.splice(index, 1);
                    }
                }
            }
        });
    /* End of controller */
})();
