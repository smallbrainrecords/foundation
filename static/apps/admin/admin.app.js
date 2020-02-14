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
    angular.module('AdminApp', ['app.services', 'myTools',
        'ngRoute', 'ngCookies', 'ngDialog', 'httpModule', 'toaster', '720kb.datepicker'])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

            $routeProvider
                .when('/', {
                    templateUrl: '/static/apps/admin/home-page/home.html',
                    controller: 'HomeCtrl'
                })
                .when('/add/user', {
                    templateUrl: '/static/apps/admin/add-user-page/add-user.html',
                    controller: 'AddUserCtrl'
                })
                .when('/edit/:userId', {
                    templateUrl: '/static/apps/admin/edit-user-page/edit-user.html',
                    controller: 'EditUserCtrl'
                })
                .when('/manage/sharing', {
                    templateUrl: '/static/apps/admin/manage-sharing-page/manage-sharing.html',
                    controller: 'ManageSharingCtrl'
                })
                .when('/manage/sharing/:patientId', {
                    templateUrl: '/static/apps/admin/manage-sharing-patient-page/manage-sharing-patient.html',
                    controller: 'ManageSharingPatientCtrl'
                })
                .when('/manage/sharing/problem/:patientId/:sharing_patient_id', {
                    templateUrl: '/static/apps/admin/manage-sharing-problem-page/manage-sharing-problem.html',
                    controller: 'ManageSharingProblemCtrl'
                }).otherwise('/');
        });
})();