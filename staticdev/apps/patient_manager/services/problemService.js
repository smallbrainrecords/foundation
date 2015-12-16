(function(){

	'use strict';

	angular.module('ManagerApp').service('problemService',
		function($http, $q, $cookies, httpService){




		this.updateProblemStatus = function(form){

			var url = '/p/problem/'+form.problem_id+'/update_status';
			return httpService.post(form, url);

		};


		this.trackProblemClickEvent = function(form){

			var url = '/p/problem/'+form.problem_id+'/track/click/';
			return httpService.post(form, url);

		};



		this.updateStartDate = function(form){

			var url = '/p/problem/'+form.problem_id+'/update_start_date';
			return httpService.post(form, url);

		};


		this.addWikiNote = function(form){

			var url = '/p/problem/'+form.problem_id+'/add_wiki_note';
			return httpService.post(form, url);

		};

		this.addHistoryNote = function(form){

			var url = '/p/problem/'+form.problem_id+'/add_history_note';
			return httpService.post(form, url);

		};

		this.addGoal = function(form){

			var url = '/p/problem/'+form.problem_id+'/add_goal';
			return httpService.post(form, url);

		};


		this.addTodo = function(form){

			var url = '/p/problem/'+form.problem_id+'/add_todo';
			return httpService.post(form, url);

		};


		this.deleteProblemImage = function(form){

			var url = '/p/problem/'+form.problem_id+'/image/'+form.image_id+'/delete/';
			return httpService.post(form, url);
		};


		this.relateProblem = function(form){

			var url = '/p/problem/relate/';
			return httpService.post(form, url);

		};

		this.getProblemActivity = function(problem_id){
			var params = {};
			var url ='/p/problem/'+problem_id+'/activity/';
			return httpService.get(params, url);
		};
});



})();