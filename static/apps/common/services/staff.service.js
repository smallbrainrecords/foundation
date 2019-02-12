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

    angular.module('app.services')
        .service('staffService', function ($q, $cookies, $http, httpService) {

            return {
                user: {},
                csrf_token: csrf_token,
                fetchActiveUser: fetchActiveUser,
                getTopPatientList: getTopPatientList,
                getPatientsList: getPatientsList,
                getUserTodoList: getUserTodoList,
                fetchPatientTodos: fetchPatientTodos,
                addToDo: addToDo,
                addToDoList: addToDoList,
                fetchLabeledTodoList: fetchLabeledTodoList,
                deleteToDoList: deleteToDoList,
                getTodosPhysicians: getTodosPhysicians,
                getAllTodos: getAllTodos,
                getSharingPatients: getSharingPatients,
                addSharingPatient: addSharingPatient,
                removeSharingPatient: removeSharingPatient,
                getUserInfo: getUserInfo,
                openTodoList: openTodoList,
                fetchProblems: fetchProblems,
                fetchSharingProblems: fetchSharingProblems,
                removeSharingProblems: removeSharingProblems,
                addSharingProblems: addSharingProblems,
                listTerms: listTerms,
                addCommonProblem: addCommonProblem,
                getCommonProblems: getCommonProblems,
                removeCommonProblem: removeCommonProblem,
                updateLastTimeAccessTaggedTodo: updateLastTimeAccessTaggedTodo,
            };

            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            function fetchActiveUser() {
                let params = {};
                let url = `/u/active/user/`;
                return httpService.get(params, url);
            }

            /**
             * Alternative getting top patient list from this.getPatientsList()
             * Supported sorting key and pagination query string
             * @param sortBy
             * @param isDescending
             * @param page
             * @param limit
             */
            function getTopPatientList(sortBy, isDescending = true, page = 0, limit = 10) {
                let form = {
                    sortBy: sortBy,
                    isDescending: isDescending,
                    page: page,
                    limit: limit
                };
                let url = `/u/patients/`;
                return httpService.post(form, url);
            }

            function getPatientsList() {
                let form = {};
                let url = `/u/patients/`;
                return httpService.post(form, url);
            }

            function getUserTodoList(user_id) {
                let form = {};
                let url = `/todo/todo/user_todos/${user_id}`;
                return httpService.post(form, url);
            }

            function fetchPatientTodos(patient_id) {

                let params = {};
                let url = `/u/patient/${patient_id}/patient_todos_info`;

                return httpService.get(params, url);

            }

            function addToDo(form) {
                let url = `/todo/staff/${form.user_id}/todos/add/new_todo`;
                return httpService.post(form, url);
            }

            function addToDoList(form) {
                let url = `/todo/staff/${form.user_id}/new_list`;
                return httpService.postJson(form, url);
            }

            function fetchLabeledTodoList(user_id) {
                let params = {};
                let url = `/todo/todo/${user_id}/getLabeledTodoList`;
                return httpService.get(params, url);
            }

            function deleteToDoList(form) {
                let url = `/todo/todo/${form.id}/deleteTodoList`;
                return httpService.post(form, url);
            }

            function getTodosPhysicians(user_id) {
                let form = {};
                let url = `/u/todos_physicians/${user_id}`;
                return httpService.post(form, url);
            }

            function getAllTodos(user_id) {
                let form = {};
                let url = `/todo/staff/all_todos/${user_id}`;
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

            function getUserInfo(user_id) {

                let params = {};
                let url = `/u/user_info/${user_id}/info/`;
                return httpService.get(params, url);

            }

            function openTodoList(form) {
                let url = `/todo/todo/${form.list_id}/open_todo_list`;
                return httpService.postJson(form, url);
            }

            function fetchProblems(patient_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/getproblems`;
                return httpService.get(params, url);
            }

            function fetchSharingProblems(patient_id, sharing_patient_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${sharing_patient_id}/get_sharing_problems`;
                return httpService.get(params, url);
            }

            function removeSharingProblems(patient_id, sharing_patient_id, problem_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${sharing_patient_id}/${problem_id}/remove_sharing_problems`;
                return httpService.post(params, url);
            }

            function addSharingProblems(patient_id, sharing_patient_id, problem_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${sharing_patient_id}/${problem_id}/add_sharing_problems`;
                return httpService.post(params, url);
            }

            function listTerms(query) {

                let params = {'query': query};
                let url = `/list_terms/`;

                return httpService.get(params, url);

            }

            function addCommonProblem(form) {
                let url = `/p/problem/staff/${form.staff_id}/add_new_common_problem`;

                return httpService.post(form, url);
            }

            function getCommonProblems(staff_id) {
                let form = {};
                let url = `/p/problem/staff/${staff_id}/get_common_problems`;

                return httpService.post(form, url);
            }

            function removeCommonProblem(problem_id) {
                let form = {};
                let url = `/p/problem/remove_common_problem/${problem_id}`;

                return httpService.post(form, url);
            }

            /**
             *
             * @param user_id
             */
            function updateLastTimeAccessTaggedTodo(user_id) {
                let params = {};
                let url = `/u/${user_id}/profile/last_access_tagged_todo`;
                return httpService.post(params, url);
            }
        });

})();