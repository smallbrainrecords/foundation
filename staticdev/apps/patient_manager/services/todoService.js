(function(){

	'use strict';

	angular.module('ManagerApp').service('todoService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){

				var token = $cookies.csrftoken;
				return token;
			};

			this.fetchTodoInfo = function(todo_id){
				var url = "/todo/todo/"+todo_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

			this.addComment = function(form){
				var url = '/todo/todo/'+form.todo_id+'/comment';

				return httpService.post(form, url);
			};

			this.editComment = function(form) {
				var url = '/todo/todo/'+form.id+'/edit';

				return httpService.post(form, url);
			};

			this.deleteComment  = function(form) {
				var url = '/todo/todo/'+form.id+'/delete';

				return httpService.post(form, url);
			};

			this.changeTodoText = function(form) {
				var url = '/todo/todo/'+form.id+'/changeText';

				return httpService.post(form, url);
			};

			this.changeTodoDueDate = function(form) {
				var url = '/todo/todo/'+form.id+'/changeDueDate';

				return httpService.post(form, url);
			};

			this.addTodoLabel = function(form) {
				var url = '/todo/todo/'+form.id+'/addLabel';

				return httpService.post(form, url);
			};

			this.removeTodoLabel = function(id) {
				var form = {};
				var url = '/todo/todo/removeLabel/'+id;

				return httpService.post(form, url);
			};

			this.addTodoAccessEncounter = function(id) {
				var form = {};
				var url = '/todo/todo/accessEncounter/'+id;

				return httpService.post(form, url);
			};

			this.addAttachment = function(form, file){
	        	var deferred = $q.defer();

	        	var uploadUrl = '/todo/todo/'+form.todo_id+'/addAttachment';

	        	var fd = new FormData();

	        	fd.append('csrfmiddlewaretoken', this.csrf_token());

	        	fd.append(0, file);
	        	

	        	$http.post(uploadUrl, fd, {
	            		transformRequest: angular.identity,
	            		headers: {'Content-Type': undefined}
	    	    	})
		        	.success(function(data){
		        		deferred.resolve(data);
	        		})
	        		.error(function(data){
	        			deferred.resolve(data);

	        		});

	        	return deferred.promise;
	    	};

	    	this.deleteAttachment  = function(form) {
				var url = '/todo/attachment/'+form.id+'/delete';

				return httpService.post(form, url);
			};
	});

})();