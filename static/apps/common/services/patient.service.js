/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
(function () {

    'use strict';


    angular.module('app.services').service('patientService',
        function ($http, $q, $cookies, $rootScope, $filter, httpService) {
            const base_url = 'u/patient/';
            return {
                activeUser: null,
                patientInfo: null,
                bleedingRisk: null,
                patientID: null,
                userID: null,
                pendingTodo: [],
                accomplishedTodo: [],
                pendingTodoPage: 1,
                accomplishedTodoPage: 1,
                accomplishedTodoLoaded: false,
                pendingTodoLoaded: false,
                loaded: 0,
                getMostRecentEncounter: getMostRecentEncounter,
                progressiveTodoLoading: progressiveTodoLoading,
                loadMoreTodo: loadMoreTodo,
                addINRTodo: addINRTodo,
                addProblemTodo: addProblemTodo,
                addTodoCallback: addTodoCallback,
                updateTodoCallback: updateTodoCallback,
                updateTodoLabel: updateTodoLabel,
                getProblemTodo: getProblemTodo,
                getColonCancerToDo: getColonCancerToDo,
                getA1CToDo: getA1CToDo,
                getINRToDo: getINRToDo,
                toggleTodoStatus: toggleTodoStatus,
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
                return $cookies.get('csrftoken');
            }

            function fetchPatientInfo(patient_id) {

                let params = {};
                let url = `/u/patient/${patient_id}/info`;

                return httpService.get(params, url);

            }

            function fetchTimeLineProblem(patient_id) {

                let params = {};
                let url = `/u/patient/${patient_id}/timelineinfo`;

                return httpService.get(params, url);

            }

            function fetchPatientTodos(patient_id) {

                let params = {};
                let url = `/u/patient/${patient_id}/patient_todos_info`;

                return httpService.get(params, url);

            }

            function fetchProblems(patient_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/getproblems`;
                return httpService.get(params, url);
            }

            function fetchProblemInfo(problem_id) {

                let url = `/p/problem/${problem_id}/info`;
                let params = {};

                return httpService.get(params, url);

            }

            function fetchGoalInfo(goal_id) {

                let url = `/g/goal/${goal_id}/info`;
                let params = {};

                return httpService.get(params, url);
            }

            function fetchEncounterInfo(encounter_id) {

                let url = `/enc/encounter/${encounter_id}/info`;
                let params = {};

                return httpService.get(params, url);


            }

            function getEncounterStatus(patient_id) {

                let url = `/enc/patient/${patient_id}/encounter/status`;
                let params = {};

                return httpService.get(params, url);


            }

            function startNewEncounter(patient_id) {


                let url = `/enc/patient/${patient_id}/encounter/start`;
                let form = {'patient_id': patient_id};

                return httpService.post(form, url);


            }

            /**
             * @deprecated
             * @param encounter_id
             */
            function stopEncounter(encounter_id) {

                let url = "/enc/encounter/" + encounter_id + "/stop";
                let params = {};

                return httpService.get(params, url);


            }

            function addEventSummary(form) {

                let url = '/enc/encounter/add/event_summary';

                return httpService.post(form, url);

            }

            function fetchPainAvatars(patient_id) {

                let url = `/patient/${patient_id}/pain_avatars`;
                let params = {};

                return httpService.get(params, url);


            }

            function listTerms(query) {

                let params = {'query': query};
                let url = "/list_terms/";

                return httpService.get(params, url);


            }

            function addGoal(form) {

                let url = `/g/patient/${form.patient_id}/goals/add/new_goal`;

                return httpService.post(form, url);

            }

            function addToDo(form) {

                let url = `/todo/patient/${form.patient_id}/todos/add/new_todo`;
                return httpService.post(form, url).then((resp) => {
                    this.pendingTodo.unshift(resp.todo);

                    $rootScope.$broadcast('todoAdded');

                    return resp;
                });
            }

            function addProblem(form) {

                let url = `/p/patient/${form.patient_id}/problems/add/new_problem`;

                return httpService.post(form, url);


            }

            function updatePatientSummary(form) {

                let url = `/u/patient/${form.patient_id}/profile/update_summary`;

                return httpService.post(form, url);

            }

            function updateTodoStatus(form) {

                let url = `/todo/todo/${form.id}/update/`;

                return httpService.post(form, url);


            }

            function fetchActiveUser() {

                let url = '/u/active/user/';
                let params = {};

                return httpService.get(params, url);

            }

            function updatePatientPassword(form) {

                let url = `/u/patient/${form.patient_id}/profile/update_password`;

                return httpService.post(form, url);

            }

            function updateBasicProfile(form) {
                let url = `/u/patient/${form.user_id}/update/basic`;
                return httpService.post(form, url);
            }

            function updateProfile(form, files) {


                let deferred = $q.defer();

                let uploadUrl = `/u/patient/${form.user_id}/update/profile`;

                let fd = new FormData();

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
                let url = `/u/patient/${form.user_id}/update/email`;
                return httpService.post(form, url);
            }

            function updateTodoOrder(form) {
                let url = '/todo/todo/updateOrder/';
                return httpService.postJson(form, url);
            }

            function updateProblemOrder(form) {
                let url = '/p/problem/updateOrder/';
                return httpService.postJson(form, url);
            }

            function updatePatientNote(form) {

                let url = `/u/patient/${form.patient_id}/profile/update_note`;

                return httpService.post(form, url);

            }

            function getPatientsList() {
                let form = {};
                let url = '/u/patients/';
                return httpService.post(form, url);
            }

            function getSharingPatients(patient_id) {
                let form = {};
                let url = `/u/sharing_patients/${patient_id}`;
                return httpService.post(form, url);
            }

            function addSharingPatient(form) {
                let url = `/u/patient/add_sharing_patient/${form.patient_id}/${form.sharing_patient_id}`;
                return httpService.post(form, url);
            }

            function removeSharingPatient(patient_id, sharing_patient_id) {
                let form = {};
                let url = `/u/patient/remove_sharing_patient/${patient_id}/${sharing_patient_id}`;
                return httpService.post(form, url);
            }

            function changeSharingMyStory(patient_id, sharing_patient_id) {
                let form = {};
                let url = `/u/patient/change_sharing_my_story/${patient_id}/${sharing_patient_id}`;
                return httpService.post(form, url);
            }

            function getUserInfo(user_id) {

                let params = {};
                let url = `/u/user_info/${user_id}/info/`;
                return httpService.get(params, url);

            }

            function addCommonProblem(form) {
                let url = `/p/patient/${form.patient_id}/problems/add/new_common_problem`;

                return httpService.post(form, url);
            }

            function getMyStory(patient_id) {
                let params = {};
                let url = `/my_story/${patient_id}/get_my_story`;
                return httpService.get(params, url);
            }

            function addMyStoryTab(form) {
                let url = `/my_story/${form.patient_id}/add_tab`;

                return httpService.post(form, url);
            }

            function addMyStoryText(form) {
                let url = `/my_story/${form.patient_id}/${form.tab_id}/add_text`;

                return httpService.post(form, url);
            }

            function getDatas(patient_id) {
                let params = {};
                let url = `/data/${patient_id}/get_datas`;
                return httpService.get(params, url);
            }

            function addNewDataType(form) {
                let url = `/data/${form.patient_id}/add_new_data_type`;

                return httpService.post(form, url);
            }

            function updateDataOrder(form) {
                let url = '/data/updateOrder';
                return httpService.postJson(form, url);
            }

            function trackDataClickEvent(form) {
                let url = '/data/track/click';
                return httpService.post(form, url);
            }

            function deleteMyStoryTab(patient_id, tab_id) {
                let form = {};
                let url = `/my_story/${patient_id}/delete_tab/${tab_id}`;

                return httpService.post(form, url);
            }

            function saveMyStoryTab(form) {
                let url = `/my_story/${form.patient_id}/save_tab/${form.tab_id}`;
                return httpService.post(form, url);
            }

            function deleteMyStoryText(patient_id, component_id) {
                let form = {};
                let url = `/my_story/${patient_id}/delete_text_component/${component_id}`;

                return httpService.post(form, url);
            }

            function saveMyStoryText(form) {
                let url = `/my_story/${form.patient_id}/save_text_component/${form.component_id}`;
                return httpService.post(form, url);
            }

            function saveMyStoryTextEntry(form) {
                let url = `/my_story/${form.patient_id}/save_text_component_entry/${form.component_id}`;
                return httpService.post(form, url);
            }

            function trackTabClickEvent(form) {
                let url = '/my_story/track/click';
                return httpService.post(form, url);
            }

            function getMedications(patient_id) {
                let params = {};
                let url = `/medication/${patient_id}/get_medications`;
                return httpService.get(params, url);
            }

            /**
             * Get list of document(s) which have ben pinned to this patient
             * by either clinical staff or patient them self
             * @param patient_id
             */
            function getDocuments(patient_id) {
                let params = {};
                let url = `/docs/${patient_id}/get_pinned_document`;
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
                }, `/u/users/${patient_id}/todos`, true)
            }

            function loadMoreTodo(patientID) {
                // Ignore if todo is fully loaded
                if (this.pendingTodoLoaded) {
                    $rootScope.$broadcast('todoListUpdated');
                    return;
                }

                httpService.get({
                    accomplished: false,
                    page: this.pendingTodoPage,
                    all: false
                }, `/u/users/${patientID}/todos`, true)
                    .then((resp) => {
                        if (resp.success) {
                            this.pendingTodoPage++;
                            // Save data to global storage
                            this.pendingTodo = this.pendingTodo.concat(resp.data);
                            this.pendingTodoLoaded = resp.data.length === 0;

                            $rootScope.$broadcast('todoListUpdated');
                        }
                    });
            }

            function addINRTodo(patientId, todo) {
                return $http.post(`/inr/${patientId}/order/add`, todo).then((resp) => {
                    this.pendingTodo.unshift(resp.data.order);

                    $rootScope.$broadcast('todoAdded');

                    return resp;
                });
            }

            function addProblemTodo(form) {
                let url = `/p/problem/${form.problem_id}/add_todo`;
                return httpService.post(form, url).then((resp) => {
                    this.pendingTodo.unshift(resp.todo);

                    $rootScope.$broadcast('todoAdded');

                    return resp;
                });
            }

            function addTodoCallback(todo) {
                /**
                 * Used to add new todo to shared store
                 * **/
                this.pendingTodo.unshift(todo);

                $rootScope.$broadcast('todoListUpdated');
            }

            function updateTodoCallback(todo) {
                angular.copy(todo, _.findWhere(this.pendingTodo, {id: parseInt(todo.id)}));
            }

            function updateTodoLabel(label, isDeleted = false) {
                _.each(this.pendingTodo, function (todo, key) {
                    if (isDeleted) {
                        todo.labels = _.reject(todo.labels, (ele) => {
                            return ele.id === parseInt(label.id)
                        });
                    } else {
                        angular.copy(label, _.findWhere(todo.labels, {id: parseInt(label.id)}));
                    }
                });

                _.each(this.accomplishedTodo, function (todo, key) {
                    if (isDeleted) {
                        todo.labels = _.reject(todo.labels, (ele) => {
                            return ele.id === parseInt(label.id)
                        });
                    } else {
                        angular.copy(label, _.findWhere(todo.labels, {id: parseInt(label.id)}));
                    }
                });
            }

            function getProblemTodo(problemID) {
                return $filter('filter')(this.pendingTodo, {problem: {id: parseInt(problemID)}}, true);
            }

            function getColonCancerToDo(problemID) {
                return _.filter(this.pendingTodo, (ele, idx) => {
                    return !_.isNull(ele.colon_cancer) && !_.isNull(ele.problem) && _.isEqual(ele.problem.id, parseInt(problemID));
                });
            }

            function getA1CToDo(problemID) {
                return _.filter(this.pendingTodo, (ele, idx) => {
                    return !_.isNull(ele.a1c) && !_.isNull(ele.problem) && _.isEqual(ele.problem.id, parseInt(problemID));
                });
            }

            function getINRToDo(problemID) {
                return $filter('filter')(this.pendingTodo, {
                    created_at: 1,
                    problem: {id: parseInt(problemID)}
                }, true);
            }

            function toggleTodoStatus(todo) {
                // Update UI data
                if (todo.accomplished) {
                    // Item is change state from pending -> accomplished
                    _.map(this.pendingTodo, (ele, idx) => {
                        if (!_.isUndefined(ele) && todo.id == ele.id) {
                            this.pendingTodo.splice(idx, 1);
                            this.accomplishedTodo.push(todo);
                        }
                    });
                } else {
                    _.map(this.accomplishedTodo, (ele, idx) => {
                        if (!_.isUndefined(ele) && todo.id == ele.id) {
                            this.accomplishedTodo.splice(idx, 1);
                            this.pendingTodo.push(todo);
                        }
                    });
                }

                // Then update API
                this.updateTodoStatus(todo).then((response) => {
                    $rootScope.$broadcast('todoListUpdated');
                });
            }

            /**
             * Load patient todo item util it fully loaded
             * @param patientID
             */
            function progressiveTodoLoading(patientID) {
                do {
                    httpService.get({
                        accomplished: false,
                        page: this.pendingTodoPage,
                        all: false
                    }, `/u/users/${patientID}/todos`, true)
                        .then((resp) => {
                            if (resp.success) {
                                this.pendingTodoPage++;
                                // Save data to global storage
                                this.pendingTodo = this.pendingTodo.concat(resp.data);
                                this.pendingTodoLoaded = resp.data.length === 0;

                                $rootScope.$broadcast('todoListUpdated');
                            }
                            // Either success of failed do reload again
                            this.progressiveTodoLoading();
                        });
                } while (this.pendingTodoLoaded);
            }


            function getMostRecentEncounter(patientID) {
                return httpService.get({}, `/u/users/${patientID}/encounters`)
            }
        });

})();