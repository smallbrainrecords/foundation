/*
 * Copyright (c) Small Brain Records 2014-2020. Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
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
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */
(function () {
    'use strict';
    angular.module('app.patientSharingModule', ['ngRoute', 'sharedModule'])
        .config(function ($routeProvider) {
            $routeProvider
                .when('/manage/sharing', {
                    templateUrl: '/static/apps/patient-sharing-module/sharing-list/sharing-list.template.html',
                    controller: 'SharingListCtrl' // Only admin and staff(s)
                })
                .when('/manage/sharing/:patientId', {
                    templateUrl: '/static/apps/patient-sharing-module/patient-sharing-page/patient-sharing-page.template.html',
                    controller: 'PatientSharingCtrl'
                })
                .when('/manage/sharing/problem/:patientId/:sharingPatientId', {
                    templateUrl: '/static/apps/patient-sharing-module/problem-sharing-page/problem-sharing-page.template.html',
                    controller: 'ProblemSharingCtrl'
                })
        });
})();

