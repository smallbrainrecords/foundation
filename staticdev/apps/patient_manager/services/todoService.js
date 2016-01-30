(function(){

	'use strict';

	angular.module('ManagerApp').service('todoService',
		function($http, $q, $cookies, httpService){


			this.fetchTodoInfo = function(todo_id){
				var url = "/todo/todo/"+todo_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

			this.addComment = function(form){
				var url = '/todo/todo/'+form.todo_id+'/comment';

				return httpService.post(form, url);
			};
	});

})();