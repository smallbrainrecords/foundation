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
        .service('colonService', function ($q, $cookies, httpService) {
            return {
                fetchColonCancerInfo: fetchColonCancerInfo,
                fetchColonCancerStudyInfo: fetchColonCancerStudyInfo,
                addNewStudy: addNewStudy,
                updateStudy: updateStudy,
                deleteStudy: deleteStudy,
                saveStudy: saveStudy,
                addFactor: addFactor,
                deleteFactor: deleteFactor,
                refuse: refuse,
                notAppropriate: notAppropriate,
                trackColonCancerClickEvent: trackColonCancerClickEvent,
                addNote: addNote,
                editNote: editNote,
                deleteNote: deleteNote
            };

            /**
             * @deprecated
             * @param colon_id
             * @returns {*}
             */
            function fetchColonCancerInfo(colon_id) {
                let url = `/colon_cancer/${colon_id}/info`;
                let params = {};

                return httpService.get(params, url);

            }

            function fetchColonCancerStudyInfo(study_id) {
                let url = `/colon_cancer/study/${study_id}/info`;
                let params = {};

                return httpService.get(params, url);

            }

            function addNewStudy(colon_id, study) {
                let url = `/colon_cancer/${colon_id}/add_study`;
                return httpService.postJson(study, url);
            }

            function deleteStudy(study) {
                let url = `/colon_cancer/${study.id}/delete_study`;
                return httpService.post(study, url);
            }

            /**
             * @deprecated
             * @param study
             * @returns {*}
             */
            function saveStudy(study) {
                let url = `/colon_cancer/${study.id}/edit_study`;
                return httpService.post(study, url);
            }

            function updateStudy(colonCancerId, studyId, study) {
                let url = `/colon_cancer/${colonCancerId}/studies/${studyId}`;
                return httpService.put(url, study);
            }

            function addFactor(colon_id, factor) {
                let url = `/colon_cancer/${colon_id}/add_factor`;
                return httpService.post(factor, url);
            }

            function deleteFactor(colon_id, factor) {
                let url = `/colon_cancer/${colon_id}/delete_factor`;
                return httpService.post(factor, url);
            }

            function refuse(colon_id) {
                let form = {};
                let url = `/colon_cancer/${colon_id}/refuse`;
                return httpService.post(form, url);
            }

            function notAppropriate(colon_id) {
                let form = {};
                let url = `/colon_cancer/${colon_id}/not_appropriate`;
                return httpService.post(form, url);
            }

            function trackColonCancerClickEvent(form) {
                let url = `/colon_cancer/${form.colon_cancer_id}/track/click`;
                return httpService.post(form, url);
            }

            function addNote(form) {
                let url = `/colon_cancer/${form.colon_cancer_id}/add_note`;
                return httpService.post(form, url);
            }

            function editNote(form) {
                let url = `/colon_cancer/note/${form.id}/edit`;

                return httpService.post(form, url);
            }

            function deleteNote(form) {
                let url = `/colon_cancer/note/${form.id}/delete`;

                return httpService.post(form, url);
            }
        });
})();