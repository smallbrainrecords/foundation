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
        .service('problemService', function ($http, $q, $cookies, httpService) {

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
                getRelatedImages: getRelatedImages,
                getProblemRelationships: getProblemRelationships,
                addNote: addNote,
                loadMoreProblemNotes: loadMoreProblemNotes
            };

            function updateProblemStatus(form) {

                let url = `/p/problem/${form.problem_id}/update_status`;
                return httpService.post(form, url);

            }

            function trackProblemClickEvent(problem_id) {
                let form = {};
                let url = `/p/problem/${problem_id}/track/click/`;
                return httpService.post(form, url);

            }

            function updateStartDate(form) {

                let url = `/p/problem/${form.problem_id}/update_start_date`;
                return httpService.post(form, url);

            }

            /**
             * @deprecated Deprecated by {@link addNote}
             * @param form
             * @returns {*}
             */
            function addWikiNote(form) {

                let url = `/p/problem/${form.problem_id}/add_wiki_note`;
                return httpService.post(form, url);

            }

            /**
             * @deprecated Deprecated by {@link addNote}
             * @param form
             * @returns {*}
             */
            function addHistoryNote(form) {

                let url = `/p/problem/${form.problem_id}/add_history_note`;
                return httpService.post(form, url);

            }

            function addGoal(form) {

                let url = `/p/problem/${form.problem_id}/add_goal`;
                return httpService.post(form, url);

            }

            function addTodo(form) {

                let url = `/p/problem/${form.problem_id}/add_todo`;
                return httpService.post(form, url);

            }

            function deleteProblemImage(form) {

                let url = `/p/problem/${form.problem_id}/image/${form.image_id}/delete/`;
                return httpService.post(form, url);
            }

            function relateProblem(form) {

                let url = '/p/problem/relate/';
                return httpService.post(form, url);

            }

            function getProblemActivity(problem_id, last_id) {
                let params = {};
                let url = `/p/problem/${problem_id}/${last_id}/activity/`;
                return httpService.get(params, url);
            }

            function updateByPTW(form) {

                let url = '/p/problem/update_by_ptw/';
                return httpService.postJson(form, url);

            }

            function updateStateToPTW(form) {

                let url = '/p/problem/update_state_to_ptw/';
                return httpService.postJson(form, url);

            }

            function changeProblemName(form) {

                let url = `/p/problem/${form.problem_id}/change_name`;

                return httpService.post(form, url);
            }

            function saveCreateLabel(problem_id, form) {
                let url = `/p/problem/newLabel/${problem_id}`;

                return httpService.post(form, url);
            }

            function fetchLabels(patient_id, user_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${user_id}/getlabels`;
                return httpService.get(params, url);
            }

            function saveEditLabel(form, patient_id, user_id) {
                let url = `/p/problem/saveEditLabel/${form.id}/${patient_id}/${user_id}`;

                return httpService.post(form, url);
            }

            function addProblemLabel(id, problem_id) {
                let form = {};
                let url = `/p/problem/${id}/${problem_id}/addLabel`;

                return httpService.post(form, url);
            }

            function removeProblemLabel(id, problem_id) {
                let form = {};
                let url = `/p/problem/removeLabel/${id}/${problem_id}`;

                return httpService.post(form, url);
            }

            function deleteLabel(form) {
                let url = `/p/problem/deleteLabel/${form.id}`;

                return httpService.post(form, url);
            }

            function addProblemList(form) {
                let url = `/p/problem/${form.patient_id}/${form.user_id}/new_list`;
                return httpService.postJson(form, url);
            }

            function fetchLabeledProblemList(patient_id, user_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${user_id}/getLabeledProblemLists`;
                return httpService.get(params, url);
            }

            function deleteProblemList(form) {
                let url = `/p/problem/${form.id}/deleteProblemList`;
                return httpService.post(form, url);
            }

            function renameProblemList(form) {
                let url = `/p/problem/${form.id}/renameProblemList`;
                return httpService.post(form, url);
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

            function updateProblemListNote(form) {
                let url = `/p/problem/${form.list_id}/update_problem_list_note`;

                return httpService.post(form, url);
            }

            function fetchA1c(problem_id) {
                let url = `/p/problem/${problem_id}/a1c`;
                let params = {};

                return httpService.get(params, url);
            }

            function fetchColonCancerss(problem_id) {
                let url = `/p/problem/${problem_id}/colon_cancers`;
                let params = {};

                return httpService.get(params, url);
            }

            function fetchPinToProblem(problem_id) {
                let url = `/p/problem/${problem_id}/get_data_pins`;
                let params = {};

                return httpService.get(params, url);
            }

            function fetchMedicationPinToProblem(problem_id) {
                let url = `/p/problem/${problem_id}/get_medication_pins`;
                let params = {};

                return httpService.get(params, url);
            }

            function deleteProblem(form) {
                let url = `/p/problem/${form.problem_id}/delete`;
                return httpService.post(form, url);
            }

            function getRelatedEncounters(problemId) {
                let url = `/p/problem/${problemId}/encounters`;
                let params = {};

                return httpService.get(params, url);
            }

            function getRelatedDocuments(problemId) {
                let url = `/p/problem/${problemId}/documents`;
                return $http.get(url);
            }

            /**
             * API to get todo of problem filter by accomplished status, and pagination
             * @param problemId
             * @param isAccomplished
             * @param page
             * @param loadAll -> This should be set item per page. 0 to load all
             */
            function getRelatedTodos(problemId, isAccomplished = false, page, loadAll = false) {
                return httpService.get({
                    accomplished: isAccomplished,
                    page: page,
                    all: loadAll
                }, `/p/problem/${problemId}/todos`);
            }

            function getRelatedGoals(problemId) {
                let url = `/p/problem/${problemId}/goals`;
                return $http.get(url);
            }

            function getRelatedWikis(problemId) {
                let url = `/p/problem/${problemId}/wikis`;
                return $http.get(url);
            }

            function getRelatedImages(problemId) {
                let url = `/p/problem/${problemId}/images`;
                return $http.get(url);
            }

            function getProblemRelationships(problemId) {
                let url = `/p/problem/${problemId}/relationships`;
                return $http.get(url);
            }

            /**
             * RESTful API to adding problem's note
             * @param {Number} problemId
             * @param {Object} data
             * @param {String} data.note
             * @param {String} data.note_type
             */
            function addNote(problemId, data) {
                let url = `/p/problem/${problemId}/notes`;
                return $http.post(url, data);
            }

            /**
             *
             * @param {Number} problemId
             * @param {String} note_type
             * @param {Number} lastItemIndex
             * @param {Number} limit
             */
            function loadMoreProblemNotes(problemId, note_type, lastItemIndex, limit) {
                let url = `/p/problem/${problemId}/notes`;
                return $http.get(url, {
                    params: {
                        type: note_type,
                        before: lastItemIndex,
                        limit: limit
                    }
                });
            }
        });
})();