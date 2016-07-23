(function () {

    'use strict';
    var blob;

    angular.module('ManagerApp')
        .controller('EncountersMainCtrl', function ($scope, $routeParams, patientService, ngDialog, $location, Upload,
                                                    encounterService, recorderService, toaster, $interval, $rootScope,
                                                    encounterRecorderFailSafeService, $window) {

            var patient_id = $('#patient_id').val();

            /**
             * Restore last unsaved session
             * @type {Array}
             */
            $scope.unsavedBlob = encounterRecorderFailSafeService.restoreUnsavedBlob();

            /**
             * Storage to store multiple recording audio file
             * @type {Array}
             */
            $scope.blobs = [];

            /**
             * Total elapsed time of audio file recorded
             * @type {number}
             */
            $scope.elapsedTime = encounterRecorderFailSafeService.restoreUnsavedDuration();

            /**
             * Maximum time in second be allowed
             * to record also encounter session
             * When this time is reached the encounter session will be stopped automatically
             * Default 90 mins
             * @type {number}
             */
            $scope.limitTime = 5400;

            /**
             * Flag determine on progress
             */
            $scope.convert_flag = false;

            /**
             * Status of the minor recorder
             * @type {boolean}
             */
            $scope.minorRecorderFlag = false;

            $scope.show_encounter_ui = false;

            $scope.patient_id = patient_id;

            $rootScope.encounter_flag = $scope.encounter_flag = false;

            /* Get Status of any running encounters */
            patientService.getEncounterStatus(patient_id).then(function (data) {

                $scope.show_encounter_ui = data['permitted'];

                if (data['encounter_active'] == true) {
                    $scope.encounter_flag = true;
                    $scope.encounter = data['current_encounter'];
                    $scope.blobs.push($scope.unsavedBlob);
                } else {
                    $scope.encounter_flag = false;
                }

            });

            $scope.start_encounter = function () {

                if ($scope.encounter_flag == true) {
                    alert("An encounter is already running!");
                } else {
                    /* Send Request is Backend */

                    patientService.startNewEncounter($scope.patient_id).then(function (data) {

                        alert('New Encounter Started');
                        $scope.encounter = data['encounter'];
                        $scope.encounter_flag = true;

                        $scope.encounterCtrl = recorderService.controller("audioInput");
                        if ($scope.encounterCtrl.status.isRecording) {
                            $scope.encounterCtrl.stopRecord();
                        }
                        $scope.encounterCtrl.startRecord();
                    });
                }
            };

            $scope.stop_encounter = function () {
                if ($scope.encounter_flag == true) {
                    var encounter_id = $scope.encounter.id;

                    patientService.stopEncounter(encounter_id).then(function (data) {

                        if (data['success'] == true) {
                            alert(data['msg']);
                            /* Encounter Stopped */
                            $scope.encounter_flag = false;

                            if ($scope.encounterCtrl.status.isRecording) {
                                $scope.encounterCtrl.stopRecord();
                            } else {
                                $scope.auto_upload();
                            }
                        } else {
                            alert(data['msg']);
                        }
                    });
                }
            };


            /**
             * Callback when recorder have finished convert dataUrl to Blob
             * and upload audio to server
             * This will not fired if the main audio is on paused state
             */
            $scope.convert_is_finished = function () {
                $scope.blobs.push($scope.encounterCtrl.audioModel);

                // Store for recovering session
                encounterRecorderFailSafeService.storeBlob($scope.encounterCtrl.audioModel, $scope.elapsedTime);

                // Will upload if the encounter is finished otherwise it will not uploaded
                if (!$scope.encounter_flag) {
                    $scope.auto_upload();
                }
            };

            /**
             * Automatically upload file
             */
            $scope.auto_upload = function () {
                var form = {};
                form.encounter_id = $scope.encounter.id;
                form.patient_id = $scope.patient_id;

                var file = new File($scope.blobs, Date.now() + ".mp3");

                encounterService.uploadAudio(form, file).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Uploaded Audio!');
                    }
                });
            };

            /**
             * Pause or Resume recorder while encounter
             */
            $scope.toggle_recorder = function () {
                // Toggle the flag
                $scope.minorRecorderFlag = !$scope.minorRecorderFlag;

                // Stop & convert the minor audio file
                $scope.encounterCtrl = $scope.encounterCtrl  || recorderService.controller("audioInput");
                $scope.encounterCtrl.status.isRecording ? $scope.encounterCtrl.stopRecord() : $scope.encounterCtrl.startRecord();
            };

            /**
             * Callback when recorder starting
             * Getting the ngRecordAudioController for globally using
             * @deprecated
             */
            $scope.record_start = function () {
                $scope.encounterCtrl = recorderService.controller("audioInput");
            };

            $scope.$watch('encounterCtrl.elapsedTime', function (newVal, oldVal) {
                $scope.elapsedTime++;
            });

            $scope.view_encounter = function () {
                var encounter_id = $scope.encounter.id;
                $location.path('/encounter/' + encounter_id);

            };


            $scope.add_event_summary = function () {

                if ($scope.event_summary.length < 1) {

                    alert("Please enter summary");
                    return false;
                }

                var form = {
                    'event_summary': $scope.event_summary,
                    'encounter_id': $scope.encounter.id
                };

                patientService.addEventSummary(form).then(function (data) {

                    if (data['success'] == true) {
                        console.log("Added event summary");

                        $scope.event_summary = '';
                    } else {
                        alert("Failed");
                    }

                });
            };

            /**
             * Track total recorded time of encounter
             */
            $scope.$watch('elapsedTime', function (newVal, oldVal) {
                if (newVal > $scope.limitTime)
                    $scope.stop_encounter();
            });

            /**
             * Show an notify message when user try to refresh | close tabs | close window
             * @param e
             * @returns {string}
             */
            $window.onbeforeunload = function (e) {
                if ($scope.encounterCtrl.status.isRecording) {

                    var confirmationMessage = "\o/"; // Due to browser security we cannot customize user message here

                    e.returnValue = confirmationMessage;     // Gecko, Trident, Chrome 34+
                    return confirmationMessage;              // Gecko, WebKit, Chrome <34
                }
            };

        });
    /* End of controller */


})();