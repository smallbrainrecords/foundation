(function () {

    'use strict';


    angular.module('ManagerApp').service('patientService',
        function ($http, $q, $cookies, httpService) {
            const base_url = 'u/patient/';
            return {
                csrf_token: csrf_token,
                fetchPatientInfo: fetchPatientInfo,
                fetchTimeLineProblem: fetchTimeLineProblem,
                fetchPatientTodos: fetchPatientTodos,
                fetchProblems: fetchProblems,
                fetchProblemInfo: fetchProblemInfo,
                fetchGoalInfo: fetchGoalInfo,
                fetchEncounterInfo: fetchEncounterInfo,
                getEncounterStatus: getEncounterStatus,
                startNewEncounter: startNewEncounter,
                stopEncounter: stopEncounter,
                addEventSummary: addEventSummary,
                fetchPainAvatars: fetchPainAvatars,
                listTerms: listTerms,
                addGoal: addGoal,
                addToDo: addToDo,
                addProblem: addProblem,
                updatePatientSummary: updatePatientSummary,
                updateTodoStatus: updateTodoStatus,
                fetchActiveUser: fetchActiveUser,
                updatePatientPassword: updatePatientPassword,
                updateBasicProfile: updateBasicProfile,
                updateProfile: updateProfile,
                updateEmail: updateEmail,
                updateTodoOrder: updateTodoOrder,
                updateProblemOrder: updateProblemOrder,
                updatePatientNote: updatePatientNote,
                getPatientsList: getPatientsList,
                getSharingPatients: getSharingPatients,
                addSharingPatient: addSharingPatient,
                removeSharingPatient: removeSharingPatient,
                changeSharingMyStory: changeSharingMyStory,
                getUserInfo: getUserInfo,
                addCommonProblem: addCommonProblem,
                getMyStory: getMyStory,
                addMyStoryTab: addMyStoryTab,
                addMyStoryText: addMyStoryText,
                getDatas: getDatas,
                addNewDataType: addNewDataType,
                updateDataOrder: updateDataOrder,
                trackDataClickEvent: trackDataClickEvent,
                deleteMyStoryTab: deleteMyStoryTab,
                saveMyStoryTab: saveMyStoryTab,
                deleteMyStoryText: deleteMyStoryText,
                saveMyStoryText: saveMyStoryText,
                saveMyStoryTextEntry: saveMyStoryTextEntry,
                trackTabClickEvent: trackTabClickEvent,
                getMedications: getMedications,
                getDocuments: getDocuments,
                getToDo: getToDo,
            };

            function csrf_token() {

                var token = $cookies.get('csrftoken');
                return token;
            }

            function fetchPatientInfo(patient_id) {

                var params = {};
                var url = '/u/patient/' + patient_id + '/info';

                return httpService.get(params, url);

            }

            function fetchTimeLineProblem(patient_id) {

                var params = {};
                var url = '/u/patient/' + patient_id + '/timelineinfo';

                return httpService.get(params, url);

            }

            function fetchPatientTodos(patient_id) {

                var params = {};
                var url = '/u/patient/' + patient_id + '/patient_todos_info';

                return httpService.get(params, url);

            }

            function fetchProblems(patient_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/getproblems';
                return httpService.get(params, url);
            }

            function fetchProblemInfo(problem_id) {

                var url = "/p/problem/" + problem_id + "/info";
                var params = {};

                return httpService.get(params, url);

            }

            function fetchGoalInfo(goal_id) {

                var url = "/g/goal/" + goal_id + "/info";
                var params = {};

                return httpService.get(params, url);
            }

            function fetchEncounterInfo(encounter_id) {

                var url = "/enc/encounter/" + encounter_id + "/info";
                var params = {};

                return httpService.get(params, url);


            }

            function getEncounterStatus(patient_id) {

                var url = "/enc/patient/" + patient_id + "/encounter/status";
                var params = {};

                return httpService.get(params, url);


            }

            function startNewEncounter(patient_id) {


                var url = '/enc/patient/' + patient_id + '/encounter/start';
                var form = {'patient_id': patient_id};

                return httpService.post(form, url);


            }

            /**
             * @deprecated
             * @param encounter_id
             */
            function stopEncounter(encounter_id) {

                var url = "/enc/encounter/" + encounter_id + "/stop";
                var params = {};

                return httpService.get(params, url);


            }

            function addEventSummary(form) {

                var url = '/enc/encounter/add/event_summary';

                return httpService.post(form, url);

            }

            function fetchPainAvatars(patient_id) {

                var url = "/patient/" + patient_id + "/pain_avatars";
                var params = {};

                return httpService.get(params, url);


            }

            function listTerms(query) {

                var params = {'query': query};
                var url = "/list_terms/";

                return httpService.get(params, url);


            }

            function addGoal(form) {

                var url = '/g/patient/' + form.patient_id + '/goals/add/new_goal';

                return httpService.post(form, url);

            }

            function addToDo(form) {

                var url = '/todo/patient/' + form.patient_id + '/todos/add/new_todo';

                return httpService.post(form, url);


            }

            function addProblem(form) {

                var url = '/p/patient/' + form.patient_id + '/problems/add/new_problem';

                return httpService.post(form, url);


            }

            function updatePatientSummary(form) {

                var url = '/u/patient/' + form.patient_id + '/profile/update_summary';

                return httpService.post(form, url);

            }

            function updateTodoStatus(form) {

                var url = '/todo/todo/' + form.id + '/update/';

                return httpService.post(form, url);


            }

            function fetchActiveUser() {

                var url = '/u/active/user/';
                var params = {};

                return httpService.get(params, url);

            }

            function updatePatientPassword(form) {

                var url = '/u/patient/' + form.patient_id + '/profile/update_password';

                return httpService.post(form, url);

            }

            function updateBasicProfile(form) {
                var url = '/u/patient/' + form.user_id + '/update/basic';
                return httpService.post(form, url);
            }

            function updateProfile(form, files) {


                var deferred = $q.defer();

                var uploadUrl = '/u/patient/' + form.user_id + '/update/profile';

                var fd = new FormData();

                fd.append('csrfmiddlewaretoken', this.csrf_token());

                angular.forEach(form, function (value, key) {
                    fd.append(key, value);
                });

                angular.forEach(files, function (value, key) {
                    fd.append(key, value);
                });


                $http.post(uploadUrl, fd, {
                    transformRequest: angular.identity,
                    headers: {'Content-Type': undefined, 'X-CSRFToken': this.csrf_token()}
                })
                    .success(function (data) {
                        deferred.resolve(data);
                    })
                    .error(function (data) {
                        deferred.resolve(data);

                    });

                return deferred.promise;
            }

            function updateEmail(form) {
                var url = '/u/patient/' + form.user_id + '/update/email';
                return httpService.post(form, url);
            }

            function updateTodoOrder(form) {
                var url = '/todo/todo/updateOrder/';
                return httpService.postJson(form, url);
            }

            function updateProblemOrder(form) {
                var url = '/p/problem/updateOrder/';
                return httpService.postJson(form, url);
            }

            function updatePatientNote(form) {

                var url = '/u/patient/' + form.patient_id + '/profile/update_note';

                return httpService.post(form, url);

            }

            function getPatientsList() {
                var form = {};
                var url = '/u/patients/';
                return httpService.post(form, url);
            }

            function getSharingPatients(patient_id) {
                var form = {};
                var url = '/u/sharing_patients/' + patient_id;
                return httpService.post(form, url);
            }

            function addSharingPatient(form) {
                var url = '/u/patient/add_sharing_patient/' + form.patient_id + '/' + form.sharing_patient_id;
                return httpService.post(form, url);
            }

            function removeSharingPatient(patient_id, sharing_patient_id) {
                var form = {};
                var url = '/u/patient/remove_sharing_patient/' + patient_id + '/' + sharing_patient_id;
                return httpService.post(form, url);
            }

            function changeSharingMyStory(patient_id, sharing_patient_id) {
                var form = {};
                var url = '/u/patient/change_sharing_my_story/' + patient_id + '/' + sharing_patient_id;
                return httpService.post(form, url);
            }

            function getUserInfo(user_id) {

                var params = {};
                var url = '/u/user_info/' + user_id + '/info/';
                return httpService.get(params, url);

            }

            function addCommonProblem(form) {
                var url = '/p/patient/' + form.patient_id + '/problems/add/new_common_problem';

                return httpService.post(form, url);
            }

            function getMyStory(patient_id) {
                var params = {};
                var url = '/my_story/' + patient_id + '/get_my_story';
                return httpService.get(params, url);
            }

            function addMyStoryTab(form) {
                var url = '/my_story/' + form.patient_id + '/add_tab';

                return httpService.post(form, url);
            }

            function addMyStoryText(form) {
                var url = '/my_story/' + form.patient_id + '/' + form.tab_id + '/add_text';

                return httpService.post(form, url);
            }

            function getDatas(patient_id) {
                var params = {};
                var url = '/data/' + patient_id + '/get_datas';
                return httpService.get(params, url);
            }

            function addNewDataType(form) {
                var url = '/data/' + form.patient_id + '/add_new_data_type';

                return httpService.post(form, url);
            }

            function updateDataOrder(form) {
                var url = '/data/updateOrder';
                return httpService.postJson(form, url);
            }

            function trackDataClickEvent(form) {
                var url = '/data/track/click';
                return httpService.post(form, url);
            }

            function deleteMyStoryTab(patient_id, tab_id) {
                var form = {};
                var url = '/my_story/' + patient_id + '/delete_tab/' + tab_id;

                return httpService.post(form, url);
            }

            function saveMyStoryTab(form) {
                var url = '/my_story/' + form.patient_id + '/save_tab/' + form.tab_id;
                return httpService.post(form, url);
            }

            function deleteMyStoryText(patient_id, component_id) {
                var form = {};
                var url = '/my_story/' + patient_id + '/delete_text_component/' + component_id;

                return httpService.post(form, url);
            }

            function saveMyStoryText(form) {
                var url = '/my_story/' + form.patient_id + '/save_text_component/' + form.component_id;
                return httpService.post(form, url);
            }

            function saveMyStoryTextEntry(form) {
                var url = '/my_story/' + form.patient_id + '/save_text_component_entry/' + form.component_id;
                return httpService.post(form, url);
            }

            function trackTabClickEvent(form) {
                var url = '/my_story/track/click';
                return httpService.post(form, url);
            }

            function getMedications(patient_id) {
                var params = {};
                var url = '/medication/' + patient_id + '/get_medications';
                return httpService.get(params, url);
            }

            /**
             * Get list of document(s) which have ben pinned to this patient
             * by either clinical staff or patient them self
             * @param patient_id
             */
            function getDocuments(patient_id) {
                var params = {};
                var url = '/docs/' + patient_id + '/get_pinned_document';
                return httpService.post(params, url);
            }


            /**
             * API to get todo by patient
             * @param patient_id
             * @param is_accomplished
             * @param page
             * @param loadAll
             * @returns {HttpPromise}
             */
            function getToDo(patient_id, is_accomplished = false, page = 1, loadAll = false) {
                return httpService.get({
                    accomplished: is_accomplished,
                    page: page,
                    all: loadAll
                }, `/u/users/${patient_id}/todos`)
            }
        });

})();