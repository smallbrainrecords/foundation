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

		this.getProblemActivity = function(problem_id, last_id){
			var params = {};
			var url ='/p/problem/' + problem_id + '/' + last_id+ '/activity/';
			return httpService.get(params, url);
		};

		this.updateByPTW = function(form){

			var url = '/p/problem/update_by_ptw/';
			return httpService.postJson(form, url);

		};

		this.updateStateToPTW = function(form){

			var url = '/p/problem/update_state_to_ptw/';
			return httpService.postJson(form, url);

		};

		this.changeProblemName = function(form){

			var url = '/p/problem/'+form.problem_id+'/change_name';

			return httpService.post(form, url);
		};

		this.saveCreateLabel = function(problem_id, form) {
			var url = '/p/problem/newLabel/'+problem_id;

			return httpService.post(form, url);
		};

		this.fetchLabels = function(patient_id, user_id){
			var params = {};
			var url ='/p/problem/' + patient_id + '/' + user_id + '/getlabels';
			return httpService.get(params, url);
		};

		this.saveEditLabel = function(form, patient_id, user_id) {
			var url = '/p/problem/saveEditLabel/' + form.id + '/' + patient_id + '/' + user_id;

			return httpService.post(form, url);
		};

		this.addProblemLabel = function(id, problem_id) {
			var form = {};
			var url = '/p/problem/'+id+'/'+problem_id+'/addLabel';

			return httpService.post(form, url);
		};

		this.removeProblemLabel = function(id, problem_id) {
			var form = {};
			var url = '/p/problem/removeLabel/'+id+'/'+problem_id;

			return httpService.post(form, url);
		};

		this.deleteLabel  = function(form) {
			var url = '/p/problem/deleteLabel/'+form.id;

			return httpService.post(form, url);
		};

		this.addProblemList = function(form){
			var url = '/p/problem/'+form.patient_id+ '/' +form.user_id+'/new_list';
			return httpService.postJson(form, url);
		};

		this.fetchLabeledProblemList = function(patient_id, user_id){
			var params = {};
			var url ='/p/problem/'+patient_id+ '/' +user_id+'/getLabeledProblemLists';
			return httpService.get(params, url);
		};

		this.deleteProblemList = function(form){
			var url = '/p/problem/'+form.id+'/deleteProblemList';
			return httpService.post(form, url);
		};

		this.renameProblemList = function(form){
			var url = '/p/problem/'+form.id+'/renameProblemList';
			return httpService.post(form, url);
		};
});



})();