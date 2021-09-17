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
            $scope.refresh_pending_users = refresh_pending_users;
            $scope.updatePendingUser = updatePendingUser;
            init();

            function init() {
                $scope.users = [];
                adminService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                    let role_form = {
                        'actor_role': $scope.active_user.role,
                        'actor_id': $scope.active_user.user.id
                    };
                    adminService.getUsersList(role_form).then(function (data) {
                        $scope.users = data;
                    });
                    adminService.getPendingRegistrationUsersList(role_form).then(function (data) {
                        $scope.pending_users = data;
                    });
                    if ($scope.active_user.role === 'physician') {
                        var form = {'physician_id': $scope.active_user.user.id};
                        adminService.getPhysicianData(form).then(function (data) {
                            $scope.patients = data['patients'];
                            $scope.team = data['team'];
                        });
                    }
                });
            }

            function refresh_pending_users() {
                adminService.getPendingRegistrationUsersList().then(function (data) {
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
