(function () {
    'use strict';

    angular.module('ManagerApp')
        .controller('EncountersMainCtrl', function ($scope, $routeParams, $interval, $rootScope, $window, $location,
                                                    ngDialog, recorderService, toaster, patientService, encounterService,
                                                    encounterRecorderFailSafeService, sharedService, RECORDER_STATUS, $indexedDB) {
            $scope.settings = sharedService.settings;
            $scope.patient_id = $('#patient_id').val();
            $scope.limitTime = 5400;

            $scope.activeEncounter = null;
            $scope.isEncounterBDFIPermitted = false; // Flag store whether or not current user can use encounter bdfi

            // $scope.encounterConverting = false;
            $scope.encounterUploading = false;
            $scope.elapsedTime = 0;
            $rootScope.encounter_flag = false;

            // Store data
            $scope.encounterCtrl = null;
            // $scope.unsavedBlob = encounterRecorderFailSafeService.restoreUnsavedBlob();
            $scope.blobs = [];
            $scope.recorderLocked = false;

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

            /**
             * Possible unhandled exception
             * $scope.patient_id is null
             * patientService.getEncounterStatus response is missing data.permitted and data.current_encounter
             * TODO: Should be implement in an more explicit way
             */
            function init() {
                $interval(function () {
                    // Periodic update encounter-bdfi recorder(this should be changed to Pub-Sub mechanism)
                    // Fetch backend command either start form tab have recorder or tab(s) don't have recorder
                    patientService.getEncounterStatus($scope.patient_id).then(data => {
                        if (data.success && data.permitted) {
                            $scope.isEncounterBDFIPermitted = data.permitted;
                            // Logged in user access validation
                            if (_.isNull(data.current_encounter)) {                                                     // Implicit ENCOUNTER STOPPED
                                // Fired stop command -> check if there is already an working worker then
                                // worker start -> worker conversion finished -> worker auto upload -> dispose in context encounter variable
                                if (_.isNull($scope.encounterCtrl)) {                                                   // Tab(s) don't have RECORDER
                                    $scope.activeEncounter = encounterService.activeEncounter = null;
                                    $scope.elapsedTime = 0
                                }
                                else {                                                                                // Tab have RECORDER
                                    $scope.activeEncounter.recorder_status = encounterService.activeEncounter.recorder_status = RECORDER_STATUS.isStopped;
                                    if ($scope.encounterCtrl.isAvailable) {
                                        // Only stop if there encounter is recording and not in converting status
                                        if ($scope.encounterCtrl.status.isRecording && !$scope.recorderLocked) {
                                            console.warn("Fetching stop");
                                            console.warn("Setting flag that recorder is received STOP the command");
                                            $scope.recorderLocked = true;
                                            $scope.encounterCtrl.stopRecord();
                                        }

                                        // Case STOP encounter from PAUSED STATE
                                        if (!$scope.encounterCtrl.status.isRecording && !$scope.encounterCtrl.status.isConverting) {
                                            console.warn("Upload audio");
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
                                        if (_.isNull($scope.encounterCtrl)) {// Tab(s) don't have recorder then do nothing. Actually it will update scope variable but we did it earlier

                                        } else {                                            // Tab have recorder then if recording stop it. if converting do nothing if not recording or converting
                                            if ($scope.encounterCtrl.status.isRecording && !$scope.encounterCtrl.status.isConverting && !$scope.recorderLocked) {
                                                console.warn("Fetching paused");
                                                console.warn("Setting flag that recorder is received PAUSE the command");
                                                $scope.recorderLocked = true;
                                                $scope.encounterCtrl.stopRecord();
                                            }
                                        }
                                        break;
                                    case RECORDER_STATUS.isRecording:
                                        if (_.isNull($scope.encounterCtrl)) {
                                            // Tab(s) don't have recorder then do nothing. Actually it will update scope variable but we did it earlier
                                        } else {
                                            // Tab have recorder
                                            if (!$scope.encounterCtrl.status.isRecording && !$scope.encounterCtrl.status.isConverting && $scope.encounterCtrl.isAvailable) {
                                                console.warn("Fetching resume");
                                                $scope.encounterCtrl.startRecord();
                                            }
                                        }
                                        break;
                                }
                            }
                        }
                    });
                }, 500);

                $interval(function () {
                    if ($scope.activeEncounter !== null && RECORDER_STATUS.isRecording === $scope.activeEncounter.recorder_status)
                        $scope.elapsedTime++;

                    // Stop encounter recorder if recorded time is reaching limitted time
                    if ($scope.elapsedTime > $scope.limitTime && $scope.encounterCtrl.status.isRecording) {
                        stopEncounter();
                    }
                }, 1000);

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
             * Whatever stop encounter button is clicked then send command to BE to stop encounter
             * Only fired command to backend
             *
             */
            function stopEncounter() {
                console.warn("stopEncounter");
                encounterService.stopEncounter(encounterService.activeEncounter.id);
            }

            function recordStart() {
                console.warn("recordStart");
            }

            function recordComplete() {
                console.warn("recordComplete");
            }

            function conversionStart() {
                console.warn("conversionStart");
            }

            function conversionComplete() {
                console.warn("conversionComplete");
                $scope.recorderLocked = false;

                switch ($scope.activeEncounter.recorder_status) {
                    case RECORDER_STATUS.isPaused:
                        encounterRecorderFailSafeService.storeBlob($scope.patient_id, $scope.encounterCtrl.audioModel, $scope.elapsedTime);
                        break;
                    case RECORDER_STATUS.isStopped:
                        uploadAudio();
                        break;
                }
            }

            /**
             * Automatically upload encounter audio file and dispose in context encounter object to update encounter-bdfi UI
             */
            function uploadAudio() {
                $scope.encounterUploading = true;
                let form = {
                    encounter_id: $scope.activeEncounter.id,
                    patient_id: $scope.patient_id
                };

                $scope.blobs.push(encounterRecorderFailSafeService.restoreUnsavedBlob($scope.patient_id));
                $scope.blobs.push($scope.encounterCtrl.audioModel);
                let file = new File($scope.blobs, Date.now() + ".mp3");
                encounterService.uploadAudio(form, file).then(data => {
                    $scope.encounterUploading = false;
                    if (data.success) {
                        toaster.pop('success', 'Done', 'Uploaded Audio!');

                        // Only dispose encounter object in tab having encounter recorder while worker success finished convert & uploaded audio file
                        $scope.activeEncounter = encounterService.activeEncounter = null;
                        $scope.blobs = [];
                        $scope.encounterCtrl = null;
                        $scope.recorderLocked = false;

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

                // if ($scope.encounterCtrl !== null) {
                // Tab have recorder
                // $scope.encounterCtrl.status.isRecording ? $scope.encounterCtrl.stopRecord() : $scope.encounterCtrl.startRecord();
                // } else {
                //    Tab(s) don't have recorder
                // }

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
                if ($scope.encounterCtrl.status.isRecording) {

                    let confirmationMessage = "\o/"; // Due to browser security we cannot customize user message here

                    e.returnValue = confirmationMessage;     // Gecko, Trident, Chrome 34+
                    return confirmationMessage;              // Gecko, WebKit, Chrome <34
                }
            }

        })
    ;
    /* End of controller */
})();