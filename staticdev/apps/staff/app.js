(function(){

	'use strict';


	var StaffApp = angular.module( 'StaffApp', 
        ['ngRoute', 'ngCookies', 'ngDialog', 'httpModule', 'myTools', 'toaster']);


    StaffApp.config(function($routeProvider) {

        $routeProvider
            .when('/', {

                templateUrl: '/static/apps/staff/partials/home.html',
                controller: 'HomeCtrl'
            });



    });


})();
