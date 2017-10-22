(function(){

	'use strict';

    angular.module('app.services')
        .service('physicianService', function ($q, $cookies, $http, httpService) {
            return {
                csrf_token: csrf_token,
                getUsersList: getUsersList,
                getPhysicianData: getPhysicianData
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
        });

})();