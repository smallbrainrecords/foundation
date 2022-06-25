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

    angular.module('app.services')
        .service('physicianService', function ($q, $cookies, $http, httpService) {
            return {
                csrf_token: csrf_token,
                getUsersList: getUsersList,
                getPhysicianData: getPhysicianData,
                getPhysicianTeam: getPhysicianTeam,
                getPhysicianPatients: getPhysicianPatients
            };

            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            function getUsersList(form) {
                let params = form;
                let url = `/project/admin/list/registered/users/`;
                return httpService.get(params, url);
            }

            function getPhysicianData(params) {

                let url = `/project/admin/physician/data/`;
                return httpService.get(params, url);
            }

            function getPhysicianTeam(params) {

                let url = `/project/admin/physician/team/`;
                return httpService.get(params, url);
            }

            function getPhysicianPatients(params) {

                let url = `/project/admin/physician/patients/`;
                return httpService.get(params, url);
            }
        });

})();