(function(){

	'use strict';


	angular.module('ManagerApp').service('patientService',
		function($http, $q, $cookies, httpService){



		this.csrf_token = function(){

			var token = $cookies.csrftoken;
			return token;
		};

		this.fetchPatientInfo = function(patient_id){

			var params = {};
			var url = '/u/patient/'+patient_id+'/info';

			return httpService.get(params, url);

		};

		this.fetchTimeLineProblem = function(patient_id){

			var params = {};
			var url = '/u/patient/'+patient_id+'/timelineinfo';

			return httpService.get(params, url);

		};

		this.fetchPatientTodos = function(patient_id){

			var params = {};
			var url = '/u/patient/'+patient_id+'/patient_todos_info';

			return httpService.get(params, url);

		};



		this.fetchProblemInfo = function(problem_id){

			var url = "/p/problem/"+problem_id+"/info";
			var params = {};

			return httpService.get(params, url);

		};


		this.fetchGoalInfo = function(goal_id){

			var url = "/g/goal/"+goal_id+"/info"
			var params = {}

			return httpService.get(params, url);
		};


		this.fetchEncounterInfo = function(encounter_id){

			var url = "/enc/encounter/"+encounter_id+"/info"
			var params = {}

			return httpService.get(params, url);


		};



		this.getEncounterStatus = function(patient_id){

			var url = "/enc/patient/"+patient_id+"/encounter/status";
			var params = {}

			return httpService.get(params, url);

			

		};

		this.startNewEncounter = function(patient_id){


			var url = '/enc/patient/'+patient_id+'/encounter/start';
			var form = { 'patient_id':patient_id };

			return httpService.post(form, url);


		};


		this.stopEncounter = function(encounter_id){

			var url = "/enc/encounter/"+encounter_id+"/stop";
			var params = {}

			return httpService.get(params, url);


		};


		this.addEventSummary = function(form){

			var url = '/enc/encounter/add/event_summary';

			return httpService.post(form, url);

		};


		this.fetchPainAvatars = function(patient_id){

			var url = "/patient/"+patient_id+"/pain_avatars";
			var params = {};

			return httpService.get(params, url);


		};


		this.listTerms = function(query){

			var params = {'query':query};
			var url = "/list_terms/";

			return httpService.get(params, url);


		};


		this.addGoal = function(form){

			var url = '/g/patient/'+form.patient_id+'/goals/add/new_goal';

			return httpService.post(form, url);

		};


		this.addToDo = function(form){

			var url = '/todo/patient/'+form.patient_id+'/todos/add/new_todo';

			return httpService.post(form, url);



		};


		this.addProblem = function(form){

			var url = '/p/patient/'+form.patient_id+'/problems/add/new_problem';

			return httpService.post(form, url);


		};


		this.updatePatientSummary = function(form){

			var url = '/u/patient/'+form.patient_id+'/profile/update_summary';

			return httpService.post(form, url);

		};


		this.updateTodoStatus = function(form){

			var url = '/todo/todo/'+ form.id + '/update/';

			return httpService.post(form, url);


		};


		this.fetchActiveUser = function(){

			var url = '/u/active/user/';
			var params = {};

			return httpService.get(params, url);

		};


		this.updatePatientPassword = function(form){

			var url = '/u/patient/'+form.patient_id+'/profile/update_password';

			return httpService.post(form, url);

		};

		this.updateBasicProfile = function(form) {
			var url = '/u/patient/'+form.user_id+'/update/basic';
			return httpService.post(form, url);
		};

		this.updateProfile = function(form, files){
        

        	var deferred = $q.defer();

        	var uploadUrl = '/u/patient/'+form.user_id+'/update/profile';

        	var fd = new FormData();

        	fd.append('csrfmiddlewaretoken', this.csrf_token());

        	angular.forEach(form, function(value, key) {
  				fd.append(key, value);
			});

        	angular.forEach(files, function(value, key){
        		fd.append(key, value);
        	});
        	

        	$http.post(uploadUrl, fd, {
            		transformRequest: angular.identity,
            		headers: {'Content-Type': undefined, 'X-CSRFToken': this.csrf_token()}
    	    	})
	        	.success(function(data){
	        		deferred.resolve(data);
        		})
        		.error(function(data){
        			deferred.resolve(data);

        		});

        	return deferred.promise;
    	};

    	this.updateEmail = function(form){
			var url = '/u/patient/'+form.user_id+'/update/email';
			return httpService.post(form, url);
		};

		this.updateTodoOrder = function(form){
			var url = '/todo/todo/updateOrder/';
			return httpService.postJson(form, url);
		};

		this.updateProblemOrder= function(form){
			var url = '/p/problem/updateOrder/';
			return httpService.postJson(form, url);
		};

		this.updatePatientNote = function(form){

			var url = '/u/patient/'+form.patient_id+'/profile/update_note';

			return httpService.post(form, url);

		};

		this.getPatientsList = function(){
			var form = {};
			var url = '/u/patients/';
			return httpService.post(form, url);
		};

		this.getSharingPatients = function(patient_id){
			var form = {};
			var url = '/u/sharing_patients/' + patient_id;
			return httpService.post(form, url);
		};

		this.addSharingPatient = function(form){
			var url = '/u/patient/add_sharing_patient/' + form.patient_id + '/' + form.sharing_patient_id;
			return httpService.post(form, url);
		};

		this.removeSharingPatient = function(patient_id, sharing_patient_id){
			var form = {};
			var url = '/u/patient/remove_sharing_patient/' + patient_id + '/' + sharing_patient_id;
			return httpService.post(form, url);
		};

		this.changeSharingMyStory = function(patient_id, sharing_patient_id){
			var form = {};
			var url = '/u/patient/change_sharing_my_story/' + patient_id + '/' + sharing_patient_id;
			return httpService.post(form, url);
		};

		this.getUserInfo = function(user_id){

			var params = {};
			var url = '/u/user_info/'+user_id+'/info/';
			return httpService.get(params, url);

		};

		this.addCommonProblem = function(form){
			var url = '/p/patient/'+form.patient_id+'/problems/add/new_common_problem';

			return httpService.post(form, url);
		};

		this.getMyStory = function(patient_id) {
			var params = {};
			var url = '/my_story/'+patient_id+'/get_my_story';
			return httpService.get(params, url);
		}

		this.addMyStoryTab = function(form){
			var url = '/my_story/'+form.patient_id+'/add_tab';

			return httpService.post(form, url);
		};

		this.addMyStoryText = function(form){
			var url = '/my_story/'+form.patient_id+ '/' +form.tab_id+'/add_text';

			return httpService.post(form, url);
		};

		this.getDatas = function(patient_id) {
			var params = {};
			var url = '/data/'+patient_id+'/get_datas';
			return httpService.get(params, url);
		}

		this.addNewDataType = function(form){
			var url = '/data/'+form.patient_id+'/add_new_data_type';

			return httpService.post(form, url);
		};

		this.updateDataOrder = function(form){
			var url = '/data/updateOrder';
			return httpService.postJson(form, url);
		};

		this.trackDataClickEvent = function(form){
			var url = '/data/track/click';
			return httpService.post(form, url);
		};

		this.deleteMyStoryTab = function(patient_id, tab_id){
			var form = {};
			var url = '/my_story/'+patient_id+'/delete_tab/' + tab_id;

			return httpService.post(form, url);
		};

		this.saveMyStoryTab = function(form){
			var url = '/my_story/'+form.patient_id+'/save_tab/' + form.tab_id;;

			return httpService.post(form, url);
		};

		this.deleteMyStoryText = function(patient_id, component_id){
			var form = {};
			var url = '/my_story/'+patient_id+'/delete_text_component/' + component_id;

			return httpService.post(form, url);
		};

		this.saveMyStoryText = function(form){
			var url = '/my_story/'+form.patient_id+'/save_text_component/' + form.component_id;;

			return httpService.post(form, url);
		};

		this.saveMyStoryTextEntry = function(form){
			var url = '/my_story/'+form.patient_id+'/save_text_component_entry/' + form.component_id;;

			return httpService.post(form, url);
		};

		this.trackTabClickEvent = function(form){
			var url = '/my_story/track/click';
			return httpService.post(form, url);
		};

		this.getInr = function(patient_id) {
			var params = {};
			var url = '/inr/'+patient_id+'/get_inr';
			return httpService.get(params, url);
		}
	});

})();