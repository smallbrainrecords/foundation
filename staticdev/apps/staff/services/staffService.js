(function () {

    'use strict';

    angular.module('StaffApp').service('staffService',
        function ($q, $cookies, $http, httpService) {
            this.user = {};

            this.csrf_token = function () {
                return $cookies.get('csrftoken');
            };

            this.fetchActiveUser = function () {
                let params = {};
                let url = '/u/active/user/';
                return httpService.get(params, url);
            };

            /**
             * Alternative getting top patient list from this.getPatientsList()
             * Supported sorting key and pagination query string
             * @param sortBy
             * @param isDescending
             * @param page
             * @param limit
             */
            this.getTopPatientList = function (sortBy, isDescending = true, page = 0, limit = 10) {
                let form = {
                    sortBy: sortBy,
                    isDescending: isDescending,
                    page: page,
                    limit: limit
                };
                let url = '/u/patients/';
                return httpService.post(form, url);
            };

            this.getPatientsList = function () {
                let form = {};
                let url = '/u/patients/';
                return httpService.post(form, url);
            };

            this.getUserTodoList = function (user_id) {
                let form = {};
                let url = '/todo/todo/user_todos/' + user_id;
                return httpService.post(form, url);
            };

            this.fetchPatientTodos = function (patient_id) {

                let params = {};
                let url = '/u/patient/' + patient_id + '/patient_todos_info';

                return httpService.get(params, url);

            };

            this.addToDo = function (form) {
                let url = '/todo/staff/' + form.user_id + '/todos/add/new_todo';
                return httpService.post(form, url);
            };

            this.addToDoList = function (form) {
                let url = '/todo/staff/' + form.user_id + '/new_list';
                return httpService.postJson(form, url);
            };

            this.fetchLabeledTodoList = function (user_id) {
                let params = {};
                let url = '/todo/todo/' + user_id + '/getLabeledTodoList';
                return httpService.get(params, url);
            };

            this.deleteToDoList = function (form) {
                let url = '/todo/todo/' + form.id + '/deleteTodoList';
                return httpService.post(form, url);
            };

            this.getTodosPhysicians = function (user_id) {
                let form = {};
                let url = '/u/todos_physicians/' + user_id;
                return httpService.post(form, url);
            };

            this.getAllTodos = function (user_id) {
                let form = {};
                let url = '/todo/staff/all_todos/' + user_id;
                return httpService.post(form, url);
            };

            this.getSharingPatients = function (patient_id) {
                let form = {};
                let url = '/u/sharing_patients/' + patient_id;
                return httpService.post(form, url);
            };

            this.addSharingPatient = function (form) {
                let url = '/u/patient/add_sharing_patient/' + form.patient_id + '/' + form.sharing_patient_id;
                return httpService.post(form, url);
            };

            this.removeSharingPatient = function (patient_id, sharing_patient_id) {
                let form = {};
                let url = '/u/patient/remove_sharing_patient/' + patient_id + '/' + sharing_patient_id;
                return httpService.post(form, url);
            };

            this.getUserInfo = function (user_id) {

                let params = {};
                let url = '/u/user_info/' + user_id + '/info/';
                return httpService.get(params, url);

            };

            this.openTodoList = function (form) {
                let url = '/todo/todo/' + form.list_id + '/open_todo_list';
                return httpService.postJson(form, url);
            };

            this.fetchProblems = function (patient_id) {
                let params = {};
                let url = '/p/problem/' + patient_id + '/getproblems';
                return httpService.get(params, url);
            };

            this.fetchSharingProblems = function (patient_id, sharing_patient_id) {
                let params = {};
                let url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/get_sharing_problems';
                return httpService.get(params, url);
            };

            this.removeSharingProblems = function (patient_id, sharing_patient_id, problem_id) {
                let params = {};
                let url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/remove_sharing_problems';
                return httpService.post(params, url);
            };

            this.addSharingProblems = function (patient_id, sharing_patient_id, problem_id) {
                let params = {};
                let url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/add_sharing_problems';
                return httpService.post(params, url);
            };

            this.listTerms = function (query) {

                let params = {'query': query};
                let url = "/list_terms/";

                return httpService.get(params, url);

            };

            this.addCommonProblem = function (form) {
                let url = '/p/problem/staff/' + form.staff_id + '/add_new_common_problem';

                return httpService.post(form, url);
            };

            this.getCommonProblems = function (staff_id) {
                let form = {};
                let url = '/p/problem/staff/' + staff_id + '/get_common_problems';

                return httpService.post(form, url);
            };

            this.removeCommonProblem = function (problem_id) {
                let form = {};
                let url = '/p/problem/remove_common_problem/' + problem_id;

                return httpService.post(form, url);
            };

            /**
             *
             * @param user_id
             */
            this.updateLastTimeAccessTaggedTodo = function (user_id) {
                let params = {};
                let url = '/u/' + user_id + '/profile/last_access_tagged_todo';
                return httpService.post(params, url);
            }
        });

})();