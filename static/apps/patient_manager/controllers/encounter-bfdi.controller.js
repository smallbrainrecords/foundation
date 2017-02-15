(function () {

    'use strict';

    angular.module('ManagerApp')
        .controller('EncountersMainCtrl', function ($scope, $routeParams, patientService, ngDialog, $location, Upload,
                                                    encounterService, recorderService, toaster, $interval, $rootScope,
                                                    encounterRecorderFailSafeService, $window, sharedService) {

            $scope.patient_id = $('#patient_id').val();
            $scope.encounterUploading = false;
            $scope.unsavedBlob = encounterRecorderFailSafeService.restoreUnsavedBlob();
            $scope.blobs = [];
            $scope.elapsedTime = 0; //encounterRecorderFailSafeService.restoreUnsavedDuration();
            $scope.limitTime = 5400;
            $scope.convert_flag = false;
            $scope.show_encounter_ui = false;
            $rootScope.encounter_flag = $scope.encounter_flag = false;
            $scope.settings = sharedService.settings;

            $scope.start_encounter = start_encounter;
            $scope.stop_encounter = stop_encounter;
            $scope.convert_is_finished = convert_is_finished;
            $scope.auto_upload = auto_upload;
            $scope.toggle_recorder = toggle_recorder;
            $scope.record_start = record_start;
            $scope.view_encounter = view_encounter;
            $scope.add_event_summary = add_event_summary;
            $window.onbeforeunload = onbeforeunload;

            init();

            function init() {

                /* Get Status of any running encounters */
                patientService.getEncounterStatus($scope.patient_id)
                    .then(function (data) {

                        $scope.show_encounter_ui = data['permitted'];

                        if (data['encounter_active'] == true) {
                            $scope.encounter_flag = true;
                            $rootScope.encounter_flag = true;
                            encounterService.activeEncounter = $scope.encounter = data['current_encounter'];
                            $scope.elapsedTime = moment().diff($scope.encounter.starttime, 'seconds');
                            $scope.blobs.push($scope.unsavedBlob);
                        } else {
                            $scope.encounter_flag = false;
                            $rootScope.encounter_flag = false;
                            encounterRecorderFailSafeService.clearUnsavedData();
                        }

                    });

                $interval(function (newVal, oldVal) {
                    $scope.elapsedTime++;
                }, 1000);

                /**
                 * Track total recorded time of encounter
                 */
                $scope.$watch('elapsedTime', function (newVal, oldVal) {
                    if (newVal >= $scope.limitTime)
                        $scope.stop_encounter();
                });
            }

            function start_encounter() {

                if ($scope.encounter_flag == true) {
                    alert("An encounter is already running!");
                } else {
                    /* Send Request is Backend */

                    patientService.startNewEncounter($scope.patient_id)
                        .then(function (response) {
                            if (response.success) {
                                toaster.pop('success', 'Done', 'New Encounter Started');

                                encounterService.activeEncounter = $scope.encounter = response.encounter;
                                $scope.encounter_flag = true;
                                $rootScope.encounter_flag = true;

                                // This section is control under general site setting
                                if (sharedService.settings.browser_audio_recording) {
                                    $scope.encounterCtrl = recorderService.controller("audioInput");
                                    if ($scope.encounterCtrl.status.isRecording) {
                                        $scope.encounterCtrl.stopRecord();
                                    }
                                    // Remove last saved session for safe
                                    encounterRecorderFailSafeService.clearUnsavedData();
                                    $scope.blobs = [];
                                    $scope.elapsedTime = 0;
                                    $scope.encounterCtrl.startRecord();
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

            function stop_encounter() {
                if ($scope.encounter_flag == true) {
                    var encounter_id = $scope.encounter.id;

                    patientService.stopEncounter(encounter_id).then(function (data) {

                        if (data['success'] == true) {
                            alert(data['msg']);
                            /* Encounter Stopped */
                            $scope.encounter_flag = false;
                            $rootScope.encounter_flag = false;

                            // This section is controlled under general site setting
                            if (sharedService.settings.browser_audio_recording) {
                                if ($scope.encounterCtrl.status.isRecording) {
                                    $scope.encounterCtrl.stopRecord();
                                } else {
                                    $scope.auto_upload();
                                }
                            }
                        } else {
                            alert(data['msg']);
                        }
                    });
                }
            }

            /**
             * Callback when recorder have finished convert dataUrl to Blob
             * and upload audio to server
             * This will not fired if the main audio is on paused state
             */
            function convert_is_finished() {
                $scope.blobs.push($scope.encounterCtrl.audioModel);

                // Store for recovering session
                encounterRecorderFailSafeService.storeBlob($scope.encounterCtrl.audioModel, $scope.elapsedTime);

                // Will upload if the encounter is finished otherwise it will not uploaded
                if (!$scope.encounter_flag) {
                    $scope.auto_upload();
                }
            }

            /**
             * Automatically upload file
             */
            function auto_upload() {
                var form = {};
                form.encounter_id = $scope.encounter.id;
                form.patient_id = $scope.patient_id;

                var file = new File($scope.blobs, Date.now() + ".mp3");
                $scope.encounterUploading = true;
                encounterService.uploadAudio(form, file)
                    .then(function (data) {
                        $scope.encounterUploading = false;

                        if (data['success'] == true) {
                            toaster.pop('success', 'Done', 'Uploaded Audio!');
                        }
                    });
            }

            /**
             * toggle_recorder
             * Pause or Resume recorder while encounter
             * Add new time stamp for later
             */
            function toggle_recorder() {
                // Stop & convert the minor audio file
                $scope.encounterCtrl = $scope.encounterCtrl || recorderService.controller("audioInput");
                $scope.encounterCtrl.status.isRecording ? $scope.encounterCtrl.stopRecord() : $scope.encounterCtrl.startRecord();

                // Create new timestamp for this encounter too
                var form = {};
                form.encounter_id = $scope.encounter.id;
                form.patient_id = $scope.patient_id;
                form.timestamp = $scope.elapsedTime;
                form.summary = $scope.encounterCtrl.status.isRecording ? "Encounter recorder paused" : "Encounter recorder resumed";
                encounterService.addTimestamp(form).then(function (data) {
                    if (data['success'] == true) {
                        $rootScope.encounter_events.push(data['encounter_event']);
                        toaster.pop('success', 'Done', 'Added timestamp!');
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                });


            }

            /**
             * Callback when recorder starting
             * Getting the ngRecordAudioController for globally using
             * @deprecated
             */
            function record_start() {
                $scope.encounterCtrl = recorderService.controller("audioInput");
            }

            function view_encounter() {
                var encounter_id = $scope.encounter.id;
                $location.path('/encounter/' + encounter_id);

            }

            function add_event_summary() {

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
            }

            /**
             * Show an notify message when user try to refresh | close tabs | close window
             * @param e
             * @returns {string}
             */
            function onbeforeunload(e) {
                if ($scope.encounterCtrl.status.isRecording) {

                    var confirmationMessage = "\o/"; // Due to browser security we cannot customize user message here

                    e.returnValue = confirmationMessage;     // Gecko, Trident, Chrome 34+
                    return confirmationMessage;              // Gecko, WebKit, Chrome <34
                }
            }

        });
    /* End of controller */


})();