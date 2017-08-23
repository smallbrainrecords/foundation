(function () {

    'use strict';

    var module = angular.module('httpModule', []).config(function ($httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });

    module.service('httpService',
        function ($http, $q, $cookies) {


            this.csrf_token = function () {
                return $cookies.get('csrftoken');
            };


            this.post = function (data, url) {

                var deferred = $q.defer();

                //data.csrfmiddlewaretoken = this.csrf_token();

                $http({
                    'method': 'POST',
                    'url': url,
                    'data': $.param(data),
                    'headers': {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-CSRFToken': this.csrf_token()
                    }
                }).success(function (data) {
                    deferred.resolve(data);
                }).error(function (data) {
                    deferred.resolve(data);
                });

                return deferred.promise;

            };

            this.postJson = function (data, url) {

                var deferred = $q.defer();

                //data.csrfmiddlewaretoken = this.csrf_token();

                $http({
                    'method': 'POST',
                    'url': url,
                    'data': data,
                    'headers': {
                        'Content-Type': 'application/json; charset=UTF-8',
                        'X-CSRFToken': this.csrf_token()
                    }
                }).success(function (data) {
                    deferred.resolve(data);
                }).error(function (data) {
                    deferred.resolve(data);
                });

                return deferred.promise;

            };

            this.get = function (params, url, cache = false) {

                let deferred = $q.defer();

                $http({
                    'method': 'GET',
                    'url': url,
                    'params': params,
                    'headers': {
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'X-CSRFToken': this.csrf_token()
                    },
                    'cache': cache
                }).success(function (data) {
                    deferred.resolve(data);
                }).error(function (data) {
                    deferred.resolve(data);
                });

                return deferred.promise;


            };

        });

})();
