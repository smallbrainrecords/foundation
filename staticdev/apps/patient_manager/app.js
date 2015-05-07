(function(){

	'use strict';


	var ManagerApp = angular.module('ManagerApp', ['ngRoute', 'ngCookies', 'ngDialog']);


    ManagerApp.config(function($routeProvider) {

        $routeProvider
            .when('/', {

                templateUrl: '/static/apps/patient_manager/partials/home.html',
                controller: 'HomeCtrl'
            });


    });


})();