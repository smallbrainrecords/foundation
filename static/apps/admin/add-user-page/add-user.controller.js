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
        .controller('AddUserCtrl', function ($scope, $routeParams, ngDialog, adminService, $location) {
            $scope.add_user = add_user;
            init();

            function init() {

                adminService.fetchActiveUser().then(function (response) {
                    let data = response.data;
                    $scope.active_user = data['user_profile'];
                });
            }

            function add_user() {
                var form = $scope.form;
                adminService.addUser(form).then(function (response) {
                    let data = response.data;
                    if (data['success'] === true) {
                        alert("User is created");
                        if ($scope.active_user.role === 'mid-level' || $scope.active_user.role === 'nurse' || $scope.active_user.role === 'secretary')
                            location.href = '/u/staff/';
                        else {
                            $location.path('/');
                        }
                    } else if (data['success'] === false) {
                        alert(data['msg']);
                        angular.forEach(data['errors'], function (value) {
                            alert(value);
                        });
                    } else {
                        alert("Something went wrong");
                    }
                });
            }
        });
    /* End of controller */
})();