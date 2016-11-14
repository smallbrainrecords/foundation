(function(){

	'use strict';

	angular.module('ManagerApp').service('inrService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){
				var token = $cookies.csrftoken;
				return token;
			};

			this.getInrs = function(patient_id, problem_id) {
				var params = {};
				var url = '/inr/'+patient_id+ '/' + problem_id +'/get_inrs';
				return httpService.get(params, url);
			}
			this.setTargetforInr = function(inr_id, target) {
				var params = {"target": target};
				var url = '/inr/'+inr_id+'/set_target';
				return httpService.get(params, url);
			}
			this.getListProblem = function(id){
				var params = {"id": id};
				var url = '/inr/get_list_problem';
				return httpService.get(params, url);
			}
			this.saveInrValue = function(datas){
				var params = {"datas": datas};
				var url = '/inr/save_inrvalue';
				return httpService.post(datas, url);
			}
			this.editInrValue = function(value, id){
				var params = {"datas": value};
				var url = '/inr/'+id+'/edit_inrvalue';
				return httpService.post(value, url);
			}
			this.deleteInrValue = function(id){
				var params = {};
				var url = '/inr/'+id+'/delete_inrvalue';
				return httpService.get(params, url);
			}
	});

})();