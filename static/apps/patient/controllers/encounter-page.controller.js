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


    angular.module('ManagerApp')
        .controller('EncounterPageCtrl', function ($scope, $rootScope, $routeParams, patientService, ngDialog,
                                                   $location, toaster, encounterService, ngAudio, prompt, $timeout) {


            $scope.encounter_id = $routeParams.encounter_id;
            $scope.encounter = {};
            $scope.encounterDocuments = [];
            $scope.related_problems = [];
            $scope.related_problems = {};

            $scope.update_note = updateNote;
            $scope.upload_video = uploadVideo;
            $scope.upload_audio = uploadAudio;
            $scope.add_timestamp = addTimestamp;
            $scope.markFavoriteEvent = markFavoriteEvent;
            $scope.unmarkFavoriteEvent = unMarkFavoriteEvent;
            $scope.nameFavoriteEvent = nameFavoriteEvent;
            $scope.deleteEncounter = deleteEncounter;
            $scope.permitted = permitted;

            init();

            function init() {
                patientService.fetchEncounterInfo($scope.encounter_id)
                    .then(function (data) {
                        $scope.encounter = data['encounter'];
                        $rootScope.encounter_events = $scope.encounter_events = data['encounter_events'];
                        $scope.encounterDocuments = data['encounter_documents'];
                        $scope.related_problems = data['related_problems'];

                        // If encounter include any audio automatically playing this audio
                        if ($scope.encounter.audio != null) {
                            $timeout(function () {
                                var myAudio = document.getElementById('audio1');
                                myAudio.onplay = function () {
                                    encounterService.updateAudioPlayedCount($scope.encounter_id);
                                };

                                if ($routeParams.startAt != null) {
                                    if (myAudio != null) {
                                        myAudio.currentTime = parseInt($routeParams.startAt);
                                        myAudio.play();
                                    }
                                }
                            }, 1000);
                        }
                    });
            }

            function updateNote() {

                var form = {};
                form.encounter_id = $scope.encounter_id;
                form.patient_id = $scope.patient_id;
                form.note = $scope.encounter.note;
                encounterService.updateNote(form).then(function (data) {
                    toaster.pop('success', 'Done', 'Updated note!');

                });


            }

            function uploadVideo() {

                var form = {};
                form.encounter_id = $scope.encounter_id;
                form.patient_id = $scope.patient_id;
                var file = $scope.video_file;

                encounterService.uploadVideo(form, file).then(function (data) {

                    if (data['success'] == true) {

                        toaster.pop('success', 'Done', 'Uploaded Video!');
                    }
                });

            }

            function uploadAudio() {

                var form = {};
                form.encounter_id = $scope.encounter_id;
                form.patient_id = $scope.patient_id;
                var file = $scope.audio_file;

                encounterService.uploadAudio(form, file).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Uploaded Audio!');
                    }
                });
            }

            function addTimestamp() {
                // Get default encounter element page
                var myAudio = document.getElementById('audio1');

                var form = {};
                form.encounter_id = $scope.encounter_id;
                form.patient_id = $scope.patient_id;
                form.timestamp = (myAudio != undefined && myAudio != null) ? myAudio.currentTime : 0;
                // form.summary = $scope.summary;
                encounterService.addTimestamp(form).then(function (data) {
                    if (data['success'] == true) {
                        $scope.encounter_events.push(data['encounter_event']);
                        toaster.pop('success', 'Done', 'Added timestamp!');
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                });
            }

            function markFavoriteEvent(encounter_event) {
                var form = {};
                form.encounter_event_id = encounter_event.id;
                form.is_favorite = true;
                encounterService.markFavoriteEvent(form).then(function (data) {
                    encounter_event.is_favorite = true;
                    toaster.pop('success', 'Done', 'Marked favorite!');
                });
            }

            function unMarkFavoriteEvent(encounter_event) {
                var form = {};
                form.encounter_event_id = encounter_event.id;
                form.is_favorite = false;
                encounterService.markFavoriteEvent(form).then(function (data) {
                    encounter_event.is_favorite = false;
                    toaster.pop('success', 'Done', 'Unmarked favorite!');
                });
            }

            function nameFavoriteEvent(encounter_event) {
                var form = {};
                form.encounter_event_id = encounter_event.id;
                form.name_favorite = encounter_event.name_favorite;
                encounterService.nameFavoriteEvent(form).then(function (data) {
                    encounter_event.is_named = false;
                    toaster.pop('success', 'Done', 'Named favorite!');
                });
            }

            function deleteEncounter() {
                prompt({
                    "title": "Are you sure?",
                    "message": "This is irreversible."
                }).then(function (result) {
                    var form = {};
                    form.encounter_id = $scope.encounter_id;
                    form.patient_id = $scope.patient_id;
                    encounterService.deleteEncounter(form).then(function (data) {
                        toaster.pop('success', 'Done', 'Deleted encounter!');
                        $location.url('/');
                    });
                }, function () {
                    return false;
                });
            }

            // TODO: Migrate to pure function
            function permitted(permissions) {

                if (_.isUndefined($scope.active_user) || _.isEmpty($scope.active_user)) {
                    return false;
                }

                var user_permissions = $scope.active_user.permissions;

                for (var key in permissions) {

                    if (user_permissions.indexOf(permissions[key]) < 0) {
                        return false;
                    }
                }

                return true;
            }
        });
})();
