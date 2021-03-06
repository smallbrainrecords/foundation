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
    angular.module('StaffApp', [
        'app.searchModule','app.patientSharingModule', 'inr', 'todos', 'document',
        'app.services', 'app.constant', 'app.directives',
        'TemplateCache', 'toaster',
        'ngRoute', 'ngCookies', 'ngDialog', 'ngAnimate', 'ngSanitize',
        'ngFileUpload', 'dndLists', 'ui.sortable', 'angular-spinkit', '720kb.datepicker', 'ui.bootstrap', 'cgPrompt',
        'view.file', 'angularMoment', 'checklist-model'])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

            $routeProvider
                .when('/', {
                    templateUrl: '/static/apps/staff/home-page/home.template.html',
                    controller: 'HomeCtrl'
                })
                .when('/manage/setting', {
                    templateUrl: '/static/apps/staff/setting-page/setting-page.html',
                    controller: 'SettingPageController'
                })
                .when("/todo/:todo_id", {
                    templateUrl: '/static/apps/staff/staff-todo-page/staff-todo-page.template.html',
                    controller: 'TodoCtrl'
                })
                .when('/manage/common_problems', {
                    templateUrl: '/static/apps/staff/problem-common-page/problem-common.template.html',
                    controller: 'ManageCommonProblemCtrl'
                })
                .when('/manage/upload_documents', {
                    templateUrl: '/static/apps/staff/upload-document-page/document-upload-page.template.html',
                    controller: 'UploadDocumentsCtrl'
                })
                .when('/manage/uploaded', {
                    templateUrl: '/static/apps/staff/uploaded-document-page/document-uploaded-page.template.html',
                    controller: 'UploadedDocumentsPageCtrl'
                })
                .when('/manage/document/:documentId', {
                    templateUrl: '/static/apps/document-detail-page/document-page.template.html',
                    controller: 'ViewDocumentCtrl'
                }).otherwise('/');
        })
        .run(($rootScope) => {
            $rootScope.$on('$routeChangeSuccess', (angularEvent, current, previous) => {
                $rootScope.currentPage = current.$$route.controller;
            });
        });
})();
