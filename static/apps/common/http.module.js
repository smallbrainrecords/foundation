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

    const module = angular.module('httpModule', ['toaster']).config(function ($httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });

    module.service('httpService', HttpService);
    HttpService.$inject = ['$http', '$q', '$cookies', 'toaster'];

    /**
     *
     * @param $http
     * @param $q
     * @param $cookies
     * @param toaster
     */
    function HttpService($http, $q, $cookies, toaster) {


        /**
         *
         * @returns {*|string}
         */
        this.csrf_token = function () {
            return $cookies.get('csrftoken');
        };


        /**
         *
         * @param data
         * @param url
         * @returns {*}
         */
        this.post = function (data, url) {

            const deferred = $q.defer();

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
                // toaster.pop('success', 'Done', 'Success');
            }).error(function (data) {
                deferred.resolve(data);
                // toaster.pop('error', 'Failed', 'Error');
            });

            return deferred.promise;

        };

        /**
         *
         * @param data
         * @param url
         * @returns {*}
         */
        this.postJson = function (data, url) {

            const deferred = $q.defer();

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

        /**
         *
         * @param params
         * @param url
         * @param cache
         * @returns {*}
         */
        this.get = function (params, url, cache = false) {

            const deferred = $q.defer();

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
        }
    }
})();