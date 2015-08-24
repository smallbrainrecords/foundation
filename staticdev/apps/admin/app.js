(function(){

	'use strict';


	var AdminApp = angular.module( 'AdminApp', 
        ['ngRoute', 'ngCookies', 'ngDialog', 'httpModule', 'myTools', 'toaster']);


    AdminApp.config(function($routeProvider) {

        $routeProvider
            .when('/', {

                templateUrl: '/static/apps/admin/partials/home.html',
                controller: 'HomeCtrl'
            })
            .when('/edit/:userId', {

                templateUrl: '/static/apps/admin/partials/edit.html',
                controller: 'EditUserCtrl'
            })
             .when('/add/user', {

                templateUrl: '/static/apps/admin/partials/add_user.html',
                controller: 'AddUserCtrl'
            });;



    });


})();
