(function () {
    'use strict';
    angular.module('app.services', ['httpModule','sharedModule'])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .run(function run($http, $cookies) {
            $http.defaults.headers.common["X-CSRFToken"] = $cookies.get('csrftoken')
        })
})();