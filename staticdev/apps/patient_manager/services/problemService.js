(function () {

    'use strict';

    angular.module('ManagerApp').service('problemService',
        function ($http, $q, $cookies, httpService) {

            return {
                updateProblemStatus: updateProblemStatus,
                trackProblemClickEvent: trackProblemClickEvent,
                updateStartDate: updateStartDate,
                addWikiNote: addWikiNote,
                addHistoryNote: addHistoryNote,
                addGoal: addGoal,
                addTodo: addTodo,
                deleteProblemImage: deleteProblemImage,
                relateProblem: relateProblem,
                getProblemActivity: getProblemActivity,
                updateByPTW: updateByPTW,
                updateStateToPTW: updateStateToPTW,
                changeProblemName: changeProblemName,
                saveCreateLabel: saveCreateLabel,
                fetchLabels: fetchLabels,
                saveEditLabel: saveEditLabel,
                addProblemLabel: addProblemLabel,
                removeProblemLabel: removeProblemLabel,
                deleteLabel: deleteLabel,
                addProblemList: addProblemList,
                fetchLabeledProblemList: fetchLabeledProblemList,
                deleteProblemList: deleteProblemList,
                renameProblemList: renameProblemList,
                fetchProblems: fetchProblems,
                fetchSharingProblems: fetchSharingProblems,
                removeSharingProblems: removeSharingProblems,
                addSharingProblems: addSharingProblems,
                updateProblemListNote: updateProblemListNote,
                fetchA1c: fetchA1c,
                fetchColonCancerss: fetchColonCancerss,
                fetchPinToProblem: fetchPinToProblem,
                fetchMedicationPinToProblem: fetchMedicationPinToProblem,
                deleteProblem: deleteProblem,
                getRelatedEncounters: getRelatedEncounters,
                getRelatedDocuments: getRelatedDocuments,
                getRelatedTodos: getRelatedTodos,
                getRelatedGoals: getRelatedGoals,
                getRelatedWikis: getRelatedWikis,
            };

            function updateProblemStatus(form) {

                var url = '/p/problem/' + form.problem_id + '/update_status';
                return httpService.post(form, url);

            }

            function trackProblemClickEvent(problem_id) {
                var form = {};
                var url = '/p/problem/' + problem_id + '/track/click/';
                return httpService.post(form, url);

            }

            function updateStartDate(form) {

                var url = '/p/problem/' + form.problem_id + '/update_start_date';
                return httpService.post(form, url);

            }

            function addWikiNote(form) {

                var url = '/p/problem/' + form.problem_id + '/add_wiki_note';
                return httpService.post(form, url);

            }

            function addHistoryNote(form) {

                var url = '/p/problem/' + form.problem_id + '/add_history_note';
                return httpService.post(form, url);

            }

            function addGoal(form) {

                var url = '/p/problem/' + form.problem_id + '/add_goal';
                return httpService.post(form, url);

            }

            function addTodo(form) {

                var url = '/p/problem/' + form.problem_id + '/add_todo';
                return httpService.post(form, url);

            }

            function deleteProblemImage(form) {

                var url = '/p/problem/' + form.problem_id + '/image/' + form.image_id + '/delete/';
                return httpService.post(form, url);
            }

            function relateProblem(form) {

                var url = '/p/problem/relate/';
                return httpService.post(form, url);

            }

            function getProblemActivity(problem_id, last_id) {
                var params = {};
                var url = '/p/problem/' + problem_id + '/' + last_id + '/activity/';
                return httpService.get(params, url);
            }

            function updateByPTW(form) {

                var url = '/p/problem/update_by_ptw/';
                return httpService.postJson(form, url);

            }

            function updateStateToPTW(form) {

                var url = '/p/problem/update_state_to_ptw/';
                return httpService.postJson(form, url);

            }

            function changeProblemName(form) {

                var url = '/p/problem/' + form.problem_id + '/change_name';

                return httpService.post(form, url);
            }

            function saveCreateLabel(problem_id, form) {
                var url = '/p/problem/newLabel/' + problem_id;

                return httpService.post(form, url);
            }

            function fetchLabels(patient_id, user_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + user_id + '/getlabels';
                return httpService.get(params, url);
            }

            function saveEditLabel(form, patient_id, user_id) {
                var url = '/p/problem/saveEditLabel/' + form.id + '/' + patient_id + '/' + user_id;

                return httpService.post(form, url);
            }

            function addProblemLabel(id, problem_id) {
                var form = {};
                var url = '/p/problem/' + id + '/' + problem_id + '/addLabel';

                return httpService.post(form, url);
            }

            function removeProblemLabel(id, problem_id) {
                var form = {};
                var url = '/p/problem/removeLabel/' + id + '/' + problem_id;

                return httpService.post(form, url);
            }

            function deleteLabel(form) {
                var url = '/p/problem/deleteLabel/' + form.id;

                return httpService.post(form, url);
            }

            function addProblemList(form) {
                var url = '/p/problem/' + form.patient_id + '/' + form.user_id + '/new_list';
                return httpService.postJson(form, url);
            }

            function fetchLabeledProblemList(patient_id, user_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + user_id + '/getLabeledProblemLists';
                return httpService.get(params, url);
            }

            function deleteProblemList(form) {
                var url = '/p/problem/' + form.id + '/deleteProblemList';
                return httpService.post(form, url);
            }

            function renameProblemList(form) {
                var url = '/p/problem/' + form.id + '/renameProblemList';
                return httpService.post(form, url);
            }

            function fetchProblems(patient_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/getproblems';
                return httpService.get(params, url);
            }

            function fetchSharingProblems(patient_id, sharing_patient_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/get_sharing_problems';
                return httpService.get(params, url);
            }

            function removeSharingProblems(patient_id, sharing_patient_id, problem_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/remove_sharing_problems';
                return httpService.post(params, url);
            }

            function addSharingProblems(patient_id, sharing_patient_id, problem_id) {
                var params = {};
                var url = '/p/problem/' + patient_id + '/' + sharing_patient_id + '/' + problem_id + '/add_sharing_problems';
                return httpService.post(params, url);
            }

            function updateProblemListNote(form) {
                var url = '/p/problem/' + form.list_id + '/update_problem_list_note';

                return httpService.post(form, url);
            }

            function fetchA1c(problem_id) {
                var url = "/p/problem/" + problem_id + "/a1c";
                var params = {};

                return httpService.get(params, url);
            }

            function fetchColonCancerss(problem_id) {
                var url = "/p/problem/" + problem_id + "/colon_cancers";
                var params = {};

                return httpService.get(params, url);
            }

            function fetchPinToProblem(problem_id) {
                var url = "/p/problem/" + problem_id + "/get_data_pins";
                var params = {};

                return httpService.get(params, url);
            }

            function fetchMedicationPinToProblem(problem_id) {
                var url = "/p/problem/" + problem_id + "/get_medication_pins";
                var params = {};

                return httpService.get(params, url);
            }

            function deleteProblem(form) {
                var url = '/p/problem/' + form.problem_id + '/delete';
                return httpService.post(form, url);
            }

            function getRelatedEncounters(problemId) {
                var url = '/p/problem/' + problemId + '/encounters ';
                var params = {};

                return httpService.get(params, url);
            }

            function getRelatedDocuments(problemId) {
                var url = '/p/problem/' + problemId + '/documents ';
                return $http.get(url);
            }

            function getRelatedTodos(problemId) {
                var url = '/p/problem/' + problemId + '/todos ';
                return $http.get(url);
            }

            function getRelatedGoals(problemId) {
                var url = '/p/problem/' + problemId + '/goals ';
                return $http.get(url);
            }

            function getRelatedWikis(problemId) {
                var url = '/p/problem/' + problemId + '/wikis ';
                return $http.get(url);
            }
        });
})();