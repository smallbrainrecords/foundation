(function(){

	'use strict';


	var ManagerApp = angular.module('ManagerApp', ['ngRoute', 'httpModule', 'ngCookies', 'ngDialog', 'myTools', 'toaster', 'ngAnimate', 'ngSanitize', 'timeLine']);


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


    });


})();