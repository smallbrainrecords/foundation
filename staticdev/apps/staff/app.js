(function () {

    'use strict';


    var StaffApp = angular.module('StaffApp', ['ngRoute', 'ngCookies', 'ngDialog', 'ngAnimate', 'ngSanitize', // Core module along with angularJS

        'sharedModule', 'httpModule', 'myTools', 'inr', 'todos', 'document', 'TemplateCache',  // Development module

        'toaster', 'ngFileUpload', 'dndLists', 'ui.sortable', // 3rd party module
        'ui.bootstrap', 'angular-click-outside', 'pickadate', 'cgPrompt', 'view.file', 'angularMoment', 'checklist-model']);


    StaffApp.config(function ($routeProvider, $httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

        $routeProvider
            .when('/', {
                templateUrl: '/static/apps/staff/partials/home.template.html',
                controller: 'HomeCtrl'
            })
            .when('/manage/setting', {
                templateUrl: '/static/apps/staff/setting-page/setting-page.html',
                controller: 'SettingPageController'
            })
            .when("/todo/:todo_id", {
                templateUrl: '/static/apps/staff/partials/staff-todo-page.template.html',
                controller: 'TodoCtrl'
            })
            .when('/manage/sharing', {

                templateUrl: '/static/apps/admin/partials/manage_sharing.html',
                controller: 'ManageSharingCtrl'
            })
            .when('/manage/sharing/:patientId', {

                templateUrl: '/static/apps/admin/partials/manage_sharing_patient.html',
                controller: 'ManageSharingPatientCtrl'
            })
            .when('/manage/sharing/problem/:patientId/:sharing_patient_id', {

                templateUrl: '/static/apps/admin/partials/manage_sharing_problem.html',
                controller: 'ManageSharingProblemCtrl'
            })
            .when('/manage/common_problems', {

                templateUrl: '/static/apps/staff/partials/problem-common.template.html',
                controller: 'ManageCommonProblemCtrl'
            })
            .when('/manage/upload_documents', {
                templateUrl: '/static/apps/document/document-upload-page.template.html',
                controller: 'UploadDocumentsCtrl'
            })
            .when('/manage/uploaded', {
                templateUrl: '/static/apps/document/document-uploaded-page.template.html',
                controller: 'UploadedDocumentsPageCtrl'
            })
            .when('/manage/document/:documentId', {
                templateUrl: '/static/apps/document/document-page.template.html',
                controller: 'ViewDocumentCtrl'
            }).otherwise('/');
    });
})();
