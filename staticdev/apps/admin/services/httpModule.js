(function(){

	'use strict';

	var module = angular.module('httpModule', []);

	module.service('httpService',
		function($http, $q, $cookies){


		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};


		this.post = function(data, url){

			var deferred = $q.defer();

			//data.csrfmiddlewaretoken = this.csrf_token();

			$http({
				'method':'POST',
				'url' : url,
				'data' : $.param(data),
				'headers':
				{
					'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
				}
			}).success(function(data){
				deferred.resolve(data);
			}).error(function(data){
				deferred.resolve(data);
			});

			return deferred.promise;

		};

		this.get = function(params, url){

			var deferred = $q.defer();

			$http({
				'method':'GET',
				'url' : url,
				'params' : $.param(params),
				'headers':
				{
					'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
				}
			}).success(function(data){
				deferred.resolve(data);
			}).error(function(data){
				deferred.resolve(data);
			});

			return deferred.promise;



		};

	});

})();
