/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
(function () {

    'use strict';

    angular.module('httpModule', ['toaster'])
        .config(function ($httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .service('httpService', HttpService);

    HttpService.$inject = ['$http', '$q', '$cookies', 'toaster'];

    /**
     *
     * @param $http
     * @param $q
     * @param $cookies
     * @param toaster
     */
    function HttpService($http, $q, $cookies, toaster) {

        this.post = function (data, url) {
            const deferred = $q.defer();

            $http({
                'method': 'POST',
                'url': url,
                'data': $.param(data),
                'headers': {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            }).success(function (data) {
                deferred.resolve(data);
            }).error(function (error) {
                console.error(`${url} --- ${JSON.stringify(data)} --- ${JSON.stringify(error)}`)
                deferred.resolve(error);
            });
            return deferred.promise;
        };


        this.postJson = function (data, url) {
            const deferred = $q.defer();

            $http({
                'method': 'POST',
                'url': url,
                'data': data,
                'headers': {
                    'Content-Type': 'application/json; charset=UTF-8',
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            }).success(function (data) {
                deferred.resolve(data);
            }).error(function (error) {
                console.error(`${url} --- ${JSON.stringify(data)} --- ${JSON.stringify(error)}`)
                deferred.resolve(error);
            });
            return deferred.promise;

        };


        this.get = function (params, url, cache = false) {

            const deferred = $q.defer();

            $http({
                'method': 'GET',
                'url': url,
                'params': params,
                'headers': {
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-CSRFToken': $cookies.get('csrftoken')
                },
                'cache': cache
            }).success(function (data) {
                deferred.resolve(data);
            }).error(function (error) {
                console.error(`${url} --- ${JSON.stringify(data)} --- ${JSON.stringify(error)}`)
                deferred.resolve(error);
            });

            return deferred.promise;
        }

        this.put = function (url, data, contentType = 'application/json; charset=UTF-8') {
            const deferred = $q.defer();
            $http({
                'method': 'PUT',
                'url': url,
                'data': data,
                'headers': {
                    'Content-Type': contentType,
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            }).success(function (data) {
                deferred.resolve(data);
            }).error(function (error) {
                console.error(`${url} --- ${JSON.stringify(data)} --- ${JSON.stringify(error)}`)
                deferred.resolve(error);
            });
            return deferred.promise;
        };

        this.delete = function (url, data) {
            const deferred = $q.defer();

            $http({
                'method': 'DELETE',
                'url': url,
                'data': data,
                'headers': {
                    'Content-Type': 'application/json; charset=UTF-8',
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            }).success(function (data) {
                deferred.resolve(data);
            }).error(function (error) {
                console.error(`${url} --- ${JSON.stringify(data)} --- ${JSON.stringify(error)}`)
                deferred.resolve(error);
            });
            return deferred.promise;
        }
    }
})();