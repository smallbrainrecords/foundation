(function(){

	'use strict';


	var AdminApp = angular.module('AdminApp', ['ngRoute', 'ngCookies', 'ngDialog', 'httpModule']);


    AdminApp.config(function($routeProvider) {

        $routeProvider
            .when('/', {

                templateUrl: '/static/apps/admin/partials/home.html',
                controller: 'HomeCtrl'
            });


    });


})();
