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
        .service('encounterService', function ($http, $q, $cookies, httpService) {
            return {
                activeEncounter: {},
                csrf_token: csrf_token,
                updateNote: updateNote,
                addTimestamp: addTimestamp,
                markFavoriteEvent: markFavoriteEvent,
                nameFavoriteEvent: nameFavoriteEvent,
                uploadAudio: uploadAudio,
                uploadVideo: uploadVideo,
                deleteEncounter: deleteEncounter,
                updateAudioPlayedCount: updateAudioPlayedCount,
                addEncounterEvent: addEncounterEvent,
                toggleRecorder: toggleRecorder,
                stopEncounter: stopEncounter,
                logEncounterAccess: logEncounterAccess
            };


            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            function updateNote(form) {

                let url = `/enc/patient/${form.patient_id}/encounter/${form.encounter_id}/update_note`;
                return httpService.post(form, url);

            }

            function addTimestamp(form) {

                let url = `/enc/patient/${form.patient_id}/encounter/${form.encounter_id}/add_timestamp`;
                return httpService.post(form, url);

            }

            function markFavoriteEvent(form) {
                let url = `/enc/encounter_event/${form.encounter_event_id}/mark_favorite`;
                return httpService.post(form, url);
            }

            function nameFavoriteEvent(form) {
                let url = `/enc/encounter_event/${form.encounter_event_id}/name_favorite`;
                return httpService.post(form, url);
            }

            function uploadAudio(form, file) {

                let deferred = $q.defer();

                let uploadUrl = `/enc/patient/${form.patient_id}/encounter/${form.encounter_id}/upload_audio/`;

                let fd = new FormData();

                angular.forEach(form, function (value, key) {
                    fd.append(key, value);
                });

                fd.append('file', file);

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

            function uploadVideo(form, file) {

                let deferred = $q.defer();

                let uploadUrl = `/enc/patient/${form.patient_id}/encounter/${form.encounter_id}/upload_video/`;

                let fd = new FormData();

                angular.forEach(form, function (value, key) {
                    fd.append(key, value);
                });

                fd.append('file', file);

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

            function deleteEncounter(form) {
                let url = `/enc/patient/${form.patient_id}/encounter/${form.encounter_id}/delete`;
                return httpService.post(form, url);
            }

            function updateAudioPlayedCount(encounterId) {
                return $http.get(`/enc/encounter/${encounterId}/audio_played`);
            }

            function addEncounterEvent(encounterId, form) {
                let url = `/enc/encounter/${encounterId}/event`;
                return httpService.post(form, url);
            }

            /**
             *
             * @param encounterId
             * @param form
             * status: 0.isRecording 1.isPaused 2.isStopped
             */
            function toggleRecorder(encounterId, form) {
                let url = `/enc/encounter/${encounterId}/recorder_status`;
                return httpService.post(form, url);
            }

            function stopEncounter(encounter_id) {

                let url = `/enc/encounter/${encounter_id}/stop`;
                let params = {};

                return httpService.get(params, url);
            }

            function logEncounterAccess(form) {
                let url = `/enc/encounter/log_access`;
                return httpService.post(form, url);
            }
        });
})();