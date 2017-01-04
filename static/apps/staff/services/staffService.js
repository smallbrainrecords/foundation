(function () {

    'use strict';

    angular.module('StaffApp').service('staffService',
        function ($q, $cookies, $http, httpService) {

            this.csrf_token = function () {
                return $cookies.get('csrftoken');
            };

            this.fetchActiveUser = function () {
                var params = {};
                var url = '/u/active/user/';
                return httpService.get(params, url);
            };

            this.getPatientsList = function () {
                var form = {};
                var url = '/u/patients/';
                return httpService.post(form, url);
            };

            this.getUserTodoList = function (user_id) {
                var form = {};
                var url = '/todo/todo/user_todos/' + user_id;
                return httpService.post(form, url);
            };

            this.fetchPatientTodos = function (patient_id) {

                var params = {};
                var url = '/u/patient/' + patient_id + '/patient_todos_info';

                return httpService.get(params, url);

            };

            this.addToDo = function (form) {
                var url = '/todo/staff/' + form.user_id + '/todos/add/new_todo';
                return httpService.post(form, url);
            };

            this.addToDoList = function (form) {
                var url = '/todo/staff/' + form.user_id + '/new_list';
                return httpService.postJson(form, url);
            };

            this.fetchLabeledTodoList = function (user_id) {
                var params = {};
                var url = '/todo/todo/' + user_id + '/getLabeledTodoList';
                return httpService.get(params, url);
            };

            this.deleteToDoList = function (form) {
                var url = '/todo/todo/' + form.id + '/deleteTodoList';
                return httpService.post(form, url);
            };

            this.getTodosPhysicians = function (user_id) {
                var form = {};
                var url = '/u/todos_physicians/' + user_id;
                return httpService.post(form, url);
            };

            this.getAllTodos = function (user_id) {
                var form = {};
                var url = '/todo/staff/all_todos/' + user_id;
                return httpService.post(form, url);
            };

            this.getSharingPatients = function (patient_id) {
                var form = {};
                var url = '/u/sharing_patients/' + patient_id;
                return httpService.post(form, url);
            };

            this.addSharingPatient = function (form) {
                var url = '/u/patient/add_sharing_patient/' + form.patient_id + '/' + form.sharing_patient_id;
                return httpService.post(form, url);
            };

            this.removeSharingPatient = function (patient_id, sharing_patient_id) {
                var form = {};
                var url = '/u/patient/remove_sharing_patient/' + patient_id + '/' + sharing_patient_id;
                return httpService.post(form, url);
            };

            this.getUserInfo = function (user_id) {

                var params = {};
                var url = '/u/user_info/' + user_id + '/info/';
                return httpService.get(params, url);

            };

            this.openTodoList = function (form) {
                var url = '/todo/todo/' + form.list_id + '/open_todo_list';
                return httpService.postJson(form, url);
            };

            this.fetchProblems = function (patient_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/getproblems';
                return httpService.get(params, url);
            };

            this.fetchSharingProblems = function (patient_id, sharing_patient_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/get_sharing_problems';
                return httpService.get(params, url);
            };

            this.removeSharingProblems = function (patient_id, sharing_patient_id, problem_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/remove_sharing_problems';
                return httpService.post(params, url);
            };

            this.addSharingProblems = function (patient_id, sharing_patient_id, problem_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/add_sharing_problems';
                return httpService.post(params, url);
            };

            this.listTerms = function (query) {

                var params = {'query': query};
                var url = "/list_terms/";

                return httpService.get(params, url);

            };

            this.addCommonProblem = function (form) {
                var url = '/p/problem/staff/' + form.staff_id + '/add_new_common_problem';

                return httpService.post(form, url);
            };

            this.getCommonProblems = function (staff_id) {
                var form = {};
                var url = '/p/problem/staff/' + staff_id + '/get_common_problems';

                return httpService.post(form, url);
            };

            this.removeCommonProblem = function (problem_id) {
                var form = {};
                var url = '/p/problem/remove_common_problem/' + problem_id;

                return httpService.post(form, url);
            };

        });

})();