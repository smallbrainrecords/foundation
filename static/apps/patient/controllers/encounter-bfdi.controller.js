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
        .controller('EncountersMainCtrl', function ($scope, $routeParams, $interval, $rootScope, $window, $location,
                                                    ngDialog, recorderService, toaster, patientService, encounterService,
                                                    encounterRecorderFailSafeService, sharedService, RECORDER_STATUS, AUDIO_UPLOAD_STATUS) {
            $scope.settings = sharedService.settings;
            $scope.limitTime = 5400;
            $scope.activeEncounter = null;
            $scope.encounterUploading = false;
            $scope.elapsedTime = 0;
            $rootScope.encounter_flag = false;
            $scope.encounterCtrl = null;
            $scope.blobs = [];
            $scope.recorderLocked = false;
            $scope.audioUploadStatus = null;

            $scope.start_encounter = startEncounter;
            $scope.stop_encounter = stopEncounter;
            $scope.toggle_recorder = toggleRecorder;
            $scope.view_encounter = viewEncounter;
            $scope.add_event_summary = addEventSummary;

            $scope.recordStart = recordStart;
            $scope.recordComplete = recordComplete;
            $scope.conversionStart = conversionStart;
            $scope.conversionComplete = conversionComplete;
            $scope.uploadAudio = uploadAudio;

            $window.onbeforeunload = onbeforeunload;

            init();

            function init() {
                $scope.elapsedTime = encounterRecorderFailSafeService.restoreUnsavedDuration();

                $interval(function () {
                    // Periodic update encounter-bdfi recorder(this should be changed to Pub-Sub mechanism)
                    // Fetch backend command either start form tab have recorder or tab(s) don't have recorder
                    patientService.getEncounterStatus($scope.patient_id).then(data => {
                        if (!_.isNull(data) && data.success && data.permitted) {
                            // Logged in user access validation
                            if (_.isNull(data.current_encounter)) { // Implicit ENCOUNTER STOPPED
                                // Fired stop command -> check if there is already an working worker then
                                // worker start -> worker conversion finished -> worker auto upload -> dispose in context encounter variable
                                if (_.isNull($scope.encounterCtrl)) {                                                   // Tab(s) don't have RECORDER
                                    $scope.activeEncounter = encounterService.activeEncounter = null;
                                    $scope.elapsedTime = 0
                                } else {                                                                                // Tab have RECORDER
                                    $scope.activeEncounter.recorder_status = encounterService.activeEncounter.recorder_status = RECORDER_STATUS.isStopped;
                                    if ($scope.encounterCtrl.isAvailable) {
                                        // Only stop if there encounter is recording and not in converting status
                                        if ($scope.encounterCtrl.status.isRecording && !$scope.recorderLocked) {
                                            console.warn("Fetching stop");
                                            console.warn("Setting flag that recorder is executed STOP command");
                                            $scope.recorderLocked = true;
                                            $scope.encounterCtrl.stopRecord();
                                        }

                                        // Case STOP encounter from PAUSED STATE
                                        // Only upload while audio is finished conversion progress and
                                        // there is no other uploading in progress
                                        if (!$scope.encounterCtrl.status.isRecording && !$scope.encounterCtrl.status.isConverting && $scope.uploadAudioStatus === AUDIO_UPLOAD_STATUS.isInitialize) {
                                            console.warn("Upload audio is fired in fetching request");
                                            console.warn("Setting flag that recorder is executed UPLOADING command");
                                            $scope.uploadAudioStatus = AUDIO_UPLOAD_STATUS.isUploading;
                                            uploadAudio();
                                        }
                                    }
                                }
                            } else { // PAUSE/RESUME/STARTING
                                // Encounter is started(resumed) or in paused status. Both either tab have or don't have recorder they will update scope variable
                                $scope.activeEncounter = encounterService.activeEncounter = data.current_encounter;
                                if ($scope.elapsedTime === 0)
                                    $scope.elapsedTime = moment().diff(data.current_encounter.starttime, 'seconds');

                                switch (data.current_encounter.recorder_status) {
                                    case RECORDER_STATUS.isPaused:
                                        // Tab(s) don't have recorder then do nothing(Actually it will update scope variable but we did it earlier)
                                        // Tab have recorder then if recording stop it. if converting do nothing if not recording or converting
                                        if (!_.isNull($scope.encounterCtrl) && $scope.encounterCtrl.status.isRecording && !$scope.encounterCtrl.status.isConverting && !$scope.recorderLocked) {
                                            console.warn("Fetching paused");
                                            console.warn("Setting flag that recorder is executed PAUSE command");
                                            $scope.recorderLocked = true;
                                            $scope.encounterCtrl.stopRecord();
                                        }
                                        break;
                                    case RECORDER_STATUS.isRecording:
                                        // Tab(s) don't have recorder then do nothing. Actually it will update scope variable but we did it earlier
                                        // Tab have recorder and the recorder is available and does not have any recording / conversion in progress then resuming(aka starting) recording session
                                        if (!_.isNull($scope.encounterCtrl) && $scope.encounterCtrl.isAvailable && !$scope.encounterCtrl.status.isRecording && !$scope.encounterCtrl.status.isConverting) {
                                            console.warn("Fetching resume");
                                            $scope.encounterCtrl.startRecord();
                                        }
                                        break;
                                    default:
                                        console.error("Unexpected recorder status");
                                        break;
                                }
                            }
                        }
                    });
                }, 3000);

                $interval(function () {
                    if ($scope.activeEncounter !== null && RECORDER_STATUS.isRecording === $scope.activeEncounter.recorder_status)
                        $scope.elapsedTime++;

                    // Stop encounter recorder if recorded time is reaching limitted time
                    if ($scope.elapsedTime > $scope.limitTime && $scope.encounterCtrl.status.isRecording) {
                        stopEncounter();
                    }
                }, 2000);

                // Update rootScope encounter status to able using in other page.
                // TODO(AnhDN): Later should be migrate to encounterService
                $scope.$watch("activeEncounter", (newVal, oldVal) => {
                    $rootScope.encounter_flag = _.isNull(newVal) ? false : _.isEqual(RECORDER_STATUS.isRecording, newVal.recorder_status);
                });
            }

            function startEncounter() {
                if (!_.isNull($scope.activeEncounter)) {
                    alert("An encounter is already running!");
                } else {
                    console.warn("startEncounter");

                    /* Send Request is Backend */
                    patientService.startNewEncounter($scope.patient_id).then(response => {
                        if (response.success) {
                            // 1st Notify that encounter is create successfully in server side and load object to scope and service
                            toaster.pop('success', 'Done', 'New Encounter Started');
                            $scope.activeEncounter = encounterService.activeEncounter = response.encounter;
                            $scope.elapsedTime = 0; // This is out of encounter recorder
                            $scope.uploadAudioStatus = AUDIO_UPLOAD_STATUS.isInitialize;

                            // 2nd Doing recorder task. This section is controlled under general site setting
                            if (sharedService.settings.browser_audio_recording) {
                                $scope.encounterCtrl = recorderService.controller("audioInput");
                                if ($scope.encounterCtrl.isAvailable) {
                                    $scope.encounterCtrl.startRecord();
                                }
                            }
                        } else {
                            ngDialog.open({
                                template: response.message,
                                plain: true
                            });
                        }
                    }, function () {
                        alert("Something are went wrong, we are fixing ASAP!");
                    });
                }
            }

            /**
             * Handler for "Stop Encounter"
             */
            function stopEncounter() {
                console.warn("stopEncounter");
                encounterService.stopEncounter(encounterService.activeEncounter.id);
            }

            /**
             * Encounter BDFI recorder start callback
             */
            function recordStart() {
                console.warn("recordStart");
            }

            /**
             * Encounter BDFI recorder complete callback
             */
            function recordComplete() {
                console.warn("recordComplete");
            }

            /**
             * Encounter BDFI conversion start callback
             */
            function conversionStart() {
                console.warn("conversionStart");
            }

            /**
             * Encounter BDFI conversion complete callback
             */
            function conversionComplete() {
                console.warn("conversionComplete");
                $scope.recorderLocked = false;

                switch ($scope.activeEncounter.recorder_status) {
                    case RECORDER_STATUS.isPaused:
                        encounterRecorderFailSafeService.storeBlob($scope.patient_id, $scope.encounterCtrl.audioModel, $scope.elapsedTime);
                        break;
                    case RECORDER_STATUS.isStopped:
                        // TODO: This method will never being reached
                        if ($scope.audioUploadStatus === AUDIO_UPLOAD_STATUS.isInitialize) {
                            console.warn("Upload audio is fired in conversion completed callback");
                            $scope.audioUploadStatus = AUDIO_UPLOAD_STATUS.isUploading;
                            uploadAudio();
                        }
                        break;
                }
            }

            /**
             * Automatically upload encounter audio file and dispose in context encounter object to update encounter-bdfi UI
             */
            function uploadAudio() {
                console.warn("Upload audio in progress...");
                // Setting the flag(s)
                $scope.encounterUploading = true;

                // Execute the request
                let form = {
                    encounter_id: $scope.activeEncounter.id,
                    patient_id: $scope.patient_id
                };
                $scope.blobs.push(encounterRecorderFailSafeService.restoreUnsavedBlob($scope.patient_id));
                $scope.blobs.push($scope.encounterCtrl.audioModel);
                let file = new File($scope.blobs, Date.now() + ".mp3");
                encounterService.uploadAudio(form, file).then(data => {
                    $scope.encounterUploading = false;
                    $scope.audioUploadStatus = AUDIO_UPLOAD_STATUS.isUploaded;

                    if (data.success) {
                        console.warn("Audio uploaded successfully...");
                        toaster.pop('success', 'Done', 'Uploaded Audio!');

                        // Only dispose encounter object in tab having encounter recorder while worker success finished convert & uploaded audio file
                        $scope.activeEncounter = encounterService.activeEncounter = null;
                        $scope.blobs = [];
                        $scope.encounterCtrl = null;
                        $scope.recorderLocked = false;
                        $scope.elapsedTime = 0;
                        encounterRecorderFailSafeService.clearUnsavedData($scope.patient_id);
                    }
                });
            }

            /**
             * toggle_recorder
             * Pause or Resume recorder while encounter
             * Add new time stamp for later
             */
            function toggleRecorder() {
                // Update encounter bdfi
                let uiForm = {
                    status: $scope.activeEncounter.recorder_status === RECORDER_STATUS.isPaused ? RECORDER_STATUS.isRecording : RECORDER_STATUS.isPaused,
                    timestamp: $scope.elapsedTime,
                    summary: $scope.activeEncounter.recorder_status === RECORDER_STATUS.isPaused ? "Encounter recorder is resumed" : "Encounter recorder is paused"
                };
                encounterService.toggleRecorder($scope.activeEncounter.id, uiForm).then(data => {
                    $scope.activeEncounter = encounterService.activeEncounter = data.current_encounter;
                });
            }

            /**
             * Go to patient's active encounter detail page
             */
            function viewEncounter() {
                $location.path('/encounter/' + encounterService.activeEncounter.id);
            }

            /**
             * Add an event summary to patient active encounter
             * @returns {boolean}
             */
            function addEventSummary() {
                // Validate data in client
                if ($scope.event_summary.length < 1) {
                    alert("Please enter summary");
                    return false;
                }

                // Save data to server
                let form = {
                    'event_summary': $scope.event_summary,
                    'encounter_id': encounterService.activeEncounter.id
                };
                patientService.addEventSummary(form).then(function (data) {
                    if (data.success) {
                        $scope.event_summary = '';
                    } else {
                        alert("You don't have permission to do this action!");
                    }
                });
            }

            /**
             * Show an notify message when user try to refresh | close tabs | close window
             * @param e
             * @returns {string}
             */
            function onbeforeunload(e) {
                if ($scope.encounterCtrl != null && $scope.encounterCtrl.hasOwnProperty('status') && $scope.encounterCtrl.status.isRecording) {
                    let confirmationMessage = "\o/"; // Due to browser security we cannot customize user message here

                    e.returnValue = confirmationMessage;     // Gecko, Trident, Chrome 34+
                    return confirmationMessage;              // Gecko, WebKit, Chrome <34
                }
            }
        });
    /* End of controller */
})();