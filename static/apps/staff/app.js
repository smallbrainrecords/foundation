(function () {

    'use strict';


    var StaffApp = angular.module('StaffApp',
        ['ngRoute', 'ngCookies', 'ngDialog', 'sharedModule', 'httpModule', 'myTools','inr',
            'toaster', 'ngAnimate', 'ngSanitize', 'ngFileUpload', 'dndLists', 'ui.sortable',
            'ui.bootstrap', 'todos', 'angular-click-outside', 'pickadate', 'cgPrompt', 'view.file']);


    StaffApp.config(function ($routeProvider) {

        $routeProvider
            .when('/', {

                templateUrl: '/static/apps/staff/partials/home.html',
                controller: 'HomeCtrl'
            })
            .when("/todo/:todo_id", {
                templateUrl: '/static/apps/staff/partials/todo.html',
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

                templateUrl: '/static/apps/staff/partials/manage_common_problems.html',
                controller: 'ManageCommonProblemCtrl'
            })
            .when('/manage/upload_documents', {
                templateUrl: '/static/apps/staff/partials/upload_documents.html',
                controller: 'UploadDocumentsCtrl'
            })
            .when('/manage/tag_document/:documentId', {
                templateUrl: '/static/apps/staff/partials/tag_document.html',
                controller: 'TagDocumentCtrl'
            });
    });

})();
