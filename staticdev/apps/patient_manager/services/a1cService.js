(function(){

	'use strict';

	angular.module('ManagerApp').service('a1cService',
		function($http, $q, $cookies, httpService){

			this.csrf_token = function(){

				var token = $cookies.csrftoken;
				return token;
			};

			this.fetchA1cInfo = function(a1c_id){
				var url = "/a1c/"+a1c_id+"/info";
				var params = {};

				return httpService.get(params, url);

			};

			this.fetchObservationComponentInfo = function(component_id){
				var url = "/a1c/"+component_id+"/component_info";
				var params = {};

				return httpService.get(params, url);

			};

			this.addNote = function(form) {
				var url = '/a1c/'+form.a1c_id+'/add_note';
				return httpService.post(form, url);
			};

			this.editNote = function(form) {
				var url = '/a1c/note/'+form.id+'/edit';

				return httpService.post(form, url);
			};

			this.deleteNote  = function(form) {
				var url = '/a1c/note/'+form.id+'/delete';

				return httpService.post(form, url);
			};

			this.addNewValue = function(form) {
				var url = '/a1c/'+form.observation_id+'/add_value';
				return httpService.post(form, url);
			};

			this.deleteValue  = function(component) {
				var url = '/a1c/component/'+component.id+'/delete';

				return httpService.post(component, url);
			};

			this.editValue  = function(form) {
				var url = '/a1c/component/'+form.component_id+'/edit';

				return httpService.post(form, url);
			};

			this.addComponentNote = function(form) {
				var url = '/a1c/component/'+form.component_id+'/add_note';
				return httpService.post(form, url);
			};

			this.editComponentNote = function(form) {
				var url = '/a1c/component/note/'+form.id+'/edit';

				return httpService.post(form, url);
			};

			this.deleteComponentNote  = function(form) {
				var url = '/a1c/component/note/'+form.id+'/delete';

				return httpService.post(form, url);
			};

			this.addValueRefused = function(form) {
				var url = '/a1c/'+form.a1c_id+'/patient_refused';
				return httpService.post(form, url);
			};

			this.trackA1cClickEvent = function(form){
				var url = '/a1c/'+form.a1c_id+'/track/click/';
				return httpService.post(form, url);
			};
	});

})();