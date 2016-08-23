(function () {

    'use strict';


    var ManagerApp = angular.module('ManagerApp', ['ngRoute', 'httpModule',
        'ngCookies', 'ngDialog', 'myTools', 'toaster', 'ngAnimate', 'ngSanitize', 'timeLine',
        'dndLists', 'ui.sortable', 'todos', 'angular-click-outside', 'mgcrea.ngStrap', 'pickadate',
        'a1c', 'colon_cancers', 'cgPrompt', 'problems', 'angularAudioRecorder', 'ngFileUpload', 'ngAudio', 'webcam']);


    ManagerApp.config(function ($routeProvider, recorderServiceProvider) {
        /**
         * Configuration for recording service
         */
        recorderServiceProvider.forceSwf(false)
            .withMp3Conversion(true, {
                bitRate: 64
            });

        $routeProvider
            .when('/', {

                templateUrl: '/static/apps/patient_manager/partials/home.html',
                controller: 'HomeCtrl'
            })
            .when('/edit/', {

                templateUrl: '/static/apps/patient_manager/partials/edit.html',
                controller: 'EditUserCtrl'
            })
            .when('/problem/:problem_id', {

                templateUrl: '/static/apps/patient_manager/partials/problem.html',
                controller: 'ProblemsCtrl'

            })
            .when('/goal/:goal_id', {

                templateUrl: '/static/apps/patient_manager/partials/goal.html',
                controller: 'GoalsCtrl'

            })
            .when('/encounter/:encounter_id', {

                templateUrl: '/static/apps/patient_manager/partials/encounter.html',
                controller: 'EncountersCtrl'

            })
            .when("/todo/:todo_id", {
                templateUrl: '/static/apps/patient_manager/partials/todo.html',
                controller: 'TodoCtrl'
            })
            .when("/a1c/:a1c_id/add_different_order", {
                templateUrl: '/static/apps/patient_manager/partials/a1c/add_different_order.html',
                controller: 'AddDifferentOrderCtrl'
            })
            .when("/a1c/:a1c_id/enter_new_value", {
                templateUrl: '/static/apps/patient_manager/partials/a1c/enter_new_value.html',
                controller: 'EnterNewValueCtrl'
            })
            .when("/a1c/:a1c_id/edit_or_delete_values", {
                templateUrl: '/static/apps/patient_manager/partials/a1c/edit_or_delete_values.html',
                controller: 'EditOrDeleteValuesCtrl'
            })
            .when("/observation_component/:component_id/edit_value", {
                templateUrl: '/static/apps/patient_manager/partials/a1c/edit_value.html',
                controller: 'EditValueCtrl'
            })
            .when('/manage/sharing', {

                templateUrl: '/static/apps/patient_manager/partials/manage_sharing_patient.html',
                controller: 'ManageSharingPatientCtrl'
            })
            .when('/manage/sharing/problem/:sharing_patient_id', {

                templateUrl: '/static/apps/patient_manager/partials/manage_sharing_problem.html',
                controller: 'ManageSharingProblemCtrl'
            })
            .when("/colon_cancer/:colon_id/add_new_study", {
                templateUrl: '/static/apps/patient_manager/partials/colon_cancer/add_new_study.html',
                controller: 'AddNewStudyCtrl'
            })
            .when("/colon_cancer/:colon_id/edit_study/:study_id", {
                templateUrl: '/static/apps/patient_manager/partials/colon_cancer/edit_study.html',
                controller: 'EditStudyCtrl'
            })
            .when("/colon_cancer/:colon_id/add_new_order", {
                templateUrl: '/static/apps/patient_manager/partials/colon_cancer/add_new_order.html',
                controller: 'AddNewOrderCtrl'
            });

    });

    ManagerApp.factory('CollapseService', function() {
        var CollapseService = {};

        CollapseService.show_colon_collapse = false;
        CollapseService.show_a1c_collapse = false;

        CollapseService.ChangeColonCollapse = function () {
           CollapseService.show_colon_collapse = !CollapseService.show_colon_collapse;
        };

        CollapseService.ChangeA1cCollapse = function () {
           CollapseService.show_a1c_collapse = !CollapseService.show_a1c_collapse;
        };

        return CollapseService;
    });


})();
