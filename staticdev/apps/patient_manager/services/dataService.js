(function(){

	'use strict';

	angular.module('ManagerApp').service('dataService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){

				var token = $cookies.csrftoken;
				return token;
			};

			this.fetchDataInfo = function(data_id){
				var url = "/data/"+data_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

	});

})();