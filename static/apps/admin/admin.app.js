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
    angular.module('AdminApp', ['ngRoute', 'ngCookies', 'ngDialog', 'httpModule', 'myTools', 'toaster', '720kb.datepicker', 'app.services'])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
            $httpProvider.defaults.transformResponse = function (data, headersGetter, status) {
                if (status = 500) {

                }
                return data;
            };

            $routeProvider
                .when('/', {
                    templateUrl: '/static/apps/admin/partials/home.html',
                    controller: 'HomeCtrl'
                })
                .when('/edit/:userId', {
                    templateUrl: '/static/apps/admin/partials/edit.html',
                    controller: 'EditUserCtrl'
                })
                .when('/add/user', {
                    templateUrl: '/static/apps/admin/partials/add_user.html',
                    controller: 'AddUserCtrl'
                })
                .when('/manage/sharing', {
                    templateUrl: '/static/apps/admin/partials/manage_sharing.html',
                    controller: 'ManageSharingCtrl'
                })
                .when('/manage/sharing/:patientId', {
                    templateUrl: '/static/apps/patient_sharing/manage_sharing_patient.html',
                    controller: 'ManageSharingPatientCtrl'
                })
                .when('/manage/sharing/problem/:patientId/:sharing_patient_id', {
                    templateUrl: '/static/apps/admin/partials/manage_sharing_problem.html',
                    controller: 'ManageSharingProblemCtrl'
                }).otherwise('/');
        });
})();