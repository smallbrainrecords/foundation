(function(){

	'use strict';


	var ManagerApp = angular.module('ManagerApp', ['ngRoute', 'httpModule', 
        'ngCookies', 'ngDialog', 'myTools', 'toaster', 'ngAnimate', 'ngSanitize', 'timeLine', 
        'dndLists', 'ui.sortable', 'todos', 'angular-click-outside', 'mgcrea.ngStrap', 'pickadate', 
        'observations', 'cgPrompt']);


    ManagerApp.config(function($routeProvider) {

        $routeProvider
            .when('/', {

                templateUrl: '/static/apps/patient_manager/partials/home.html',
                controller: 'HomeCtrl'
            })
            .when('/edit/', {

                templateUrl: '/static/apps/patient_manager/partials/edit.html',
                controller: 'EditUserCtrl'
            })
            .when('/problem/:problem_id',{

            	templateUrl: '/static/apps/patient_manager/partials/problem.html',
                controller: 'ProblemsCtrl'

            })
            .when('/goal/:goal_id',{

                templateUrl: '/static/apps/patient_manager/partials/goal.html',
                controller: 'GoalsCtrl'

            })
            .when('/encounter/:encounter_id',{

                templateUrl: '/static/apps/patient_manager/partials/encounter.html',
                controller: 'EncountersCtrl'

            })
            .when("/todo/:todo_id", {
                templateUrl: '/static/apps/patient_manager/partials/todo.html',
                controller: 'TodoCtrl'
            })
            .when("/observation/:observation_id/add_different_order", {
                templateUrl: '/static/apps/patient_manager/partials/observation/add_different_order.html',
                controller: 'AddDifferentOrderCtrl'
            })
            .when("/observation/:observation_id/enter_new_value", {
                templateUrl: '/static/apps/patient_manager/partials/observation/enter_new_value.html',
                controller: 'EnterNewValueCtrl'
            })
            .when("/observation/:observation_id/edit_or_delete_values", {
                templateUrl: '/static/apps/patient_manager/partials/observation/edit_or_delete_values.html',
                controller: 'EditOrDeleteValuesCtrl'
            })
            .when("/observation_component/:component_id/edit_value", {
                templateUrl: '/static/apps/patient_manager/partials/observation/edit_value.html',
                controller: 'EditValueCtrl'
            });

    });


})();