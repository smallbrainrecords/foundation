(function () {
    /***
     * DISCLAIMER This component is under development
     */
    'use strict';

    angular.module('ManagerApp')
        .controller('EncountersMainCtrl', function ($scope, $routeParams, patientService, ngDialog, $location, Upload,
                                                    encounterService, recorderService, toaster, $interval, $rootScope,
                                                    encounterRecorderFailSafeService, $window, sharedService) {

            $scope.settings = sharedService.settings;

            $scope.patient_id = $('#patient_id').val();
            $scope.encounterUploading = false;

            $scope.elapsedTime = 0;
            $scope.limitTime = 5400;

            $scope.convert_flag = false;
            $scope.unsavedBlob = encounterRecorderFailSafeService.restoreUnsavedBlob();
            $scope.blobs = [];
            $scope.show_encounter_ui = false;
            $rootScope.encounter_flag = $scope.encounter_flag = false;
            // Flag which determine is this tab
            $scope.isPrimaryEncounterRecording = false;

            $scope.start_encounter = startEncounter;
            $scope.stop_encounter = stopEncounter;
            $scope.convert_is_finished = convertIsFinished;
            $scope.auto_upload = autoUpload;
            $scope.toggle_recorder = toggleRecorder;
            $scope.record_start = recordStart;
            $scope.view_encounter = viewEncounter;
            $scope.add_event_summary = addEventSummary;
            $window.onbeforeunload = onbeforeunload;

            init();

            function init() {

                /* Get Status of any running encounters */
                function uiStartEncounter(data) {
                    $scope.encounter_flag = $rootScope.encounter_flag = true;
                    encounterService.activeEncounter = $scope.encounter = data['current_encounter'];
                    $scope.elapsedTime = moment().diff($scope.encounter.starttime, 'seconds');
                    $scope.blobs.push($scope.unsavedBlob);
                }


                patientService.getEncounterStatus($scope.patient_id).then(function (data) {
                    $scope.show_encounter_ui = data['permitted'];

                    if (data.encounter_active) {
                        uiStartEncounter(data);
                    } else {
                        uiStopEncounter();
                    }

                });

                $interval(function () {
                    $scope.elapsedTime++;

                    // Periodic checking encounter recording status
                    // TODO: Later this should be changed to Pub-Sub mechanism
                    patientService.getEncounterStatus($scope.patient_id).then(function (data) {
                        if (data.encounter_active) {
                            uiStartEncounter(data);
                        } else {
                            if ($scope.isPrimaryEncounterRecording)
                                $scope.stop_encounter();

                            // Must be followed after doing converting & upload work cuz use of
                            // this flag $scope.isPrimaryEncounterRecording = false;
                            uiStopEncounter();
                        }
                    });
                }, 1000);

                /**
                 * Track total recorded time of encounter
                 */
                $scope.$watch('elapsedTime', function (newVal, oldVal) {
                    if (newVal >= $scope.limitTime)
                        $scope.stop_encounter();
                });
            }

            function uiStopEncounter() {
                $scope.encounter_flag = $rootScope.encounter_flag = false;
                encounterRecorderFailSafeService.clearUnsavedData();
                // TODO: Becareful while using this flag it may cause some function not working
                // $scope.isPrimaryEncounterRecording = false;
            }

            function startEncounter() {
                if ($scope.encounter_flag) {
                    alert("An encounter is already running!");
                } else {
                    /* Send Request is Backend */
                    patientService.startNewEncounter($scope.patient_id)
                        .then(function (response) {
                            if (response.success) {
                                toaster.pop('success', 'Done', 'New Encounter Started');

                                $scope.isPrimaryEncounterRecording = true;
                                $scope.encounter_flag = $rootScope.encounter_flag = true;
                                encounterService.activeEncounter = $scope.encounter = response.encounter;

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

            function stopEncounter() {
                patientService.stopEncounter($scope.encounter.id)
                    .then(function (data) {
                        if (data.success) {
                            // This section is controlled under general site setting only request to upload and convert
                            if (sharedService.settings.browser_audio_recording && $scope.isPrimaryEncounterRecording) {
                                if ($scope.encounterCtrl.status.isRecording) {
                                    $scope.encounterCtrl.stopRecord();
                                } else {
                                    $scope.auto_upload();
                                }

                                $scope.isPrimaryEncounterRecording = false;
                            }

                            // Encounter Stopped update UI page. Reset flag(s)
                            uiStopEncounter();

                        } else {
                            alert(data['msg']);
                        }
                    });
            }

            /**
             * Callback when recorder have finished convert dataUrl to Blob
             * and upload audio to server
             * This will not fired if the main audio is on paused state
             */
            function convertIsFinished() {
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
            function autoUpload() {
                let form = {};
                form.encounter_id = $scope.encounter.id;
                form.patient_id = $scope.patient_id;

                let file = new File($scope.blobs, Date.now() + ".mp3");
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
            function toggleRecorder() {
                // Stop & convert the minor audio file
                $scope.encounterCtrl = $scope.encounterCtrl || recorderService.controller("audioInput");
                $scope.encounterCtrl.status.isRecording ? $scope.encounterCtrl.stopRecord() : $scope.encounterCtrl.startRecord();

                // Create new timestamp for this encounter too
                let form = {
                    encounter_id: $scope.encounter.id,
                    patient_id: $scope.patient_id,
                    timestamp: $scope.elapsedTime,
                    summary: $scope.encounterCtrl.status.isRecording ? "Encounter recorder paused" : "Encounter recorder resumed"
                };
                encounterService.addTimestamp(form).then(function (data) {
                    if (data.success) {
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
            function recordStart() {
                $scope.encounterCtrl = recorderService.controller("audioInput");
            }

            function viewEncounter() {
                $location.path('/encounter/' + $scope.encounter.id);
            }

            function addEventSummary() {

                if ($scope.event_summary.length < 1) {

                    alert("Please enter summary");
                    return false;
                }

                let form = {
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

                    let confirmationMessage = "\o/"; // Due to browser security we cannot customize user message here

                    e.returnValue = confirmationMessage;     // Gecko, Trident, Chrome 34+
                    return confirmationMessage;              // Gecko, WebKit, Chrome <34
                }
            }

        });
    /* End of controller */
})();