(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('ManageSharingPatientCtrl', function ($scope, $routeParams, ngDialog, staffService, $location, $anchorScroll, toaster, inrService) {

            $scope.patientName = '';
            // $scope.patient_id = $routeParams['patientId'];
            $scope.assign_patient_form = {};
            // $scope.patient = $scope.patient_info;

            $scope.findPatient = findPatient;

            $scope.add_sharing_patient = add_sharing_patient;
            $scope.remove_sharing_patient = remove_sharing_patient;
            $scope.permitted = permitted;
            $scope.isShared = isShared;

            init();

            function init() {

                // staffService.fetchActiveUser().then(function (data) {
                //     $scope.active_user = data['user_profile'];
                // });

                staffService.getUserInfo($scope.patient_id).then(function (data) {
                    $scope.patient = data['user_profile'];
                });

                staffService.getSharingPatients($scope.patient_id).then(function (data) {
                    $scope.sharing_patients = data['sharing_patients'];
                });

            }

            function add_sharing_patient(sharingPatientId) {
                let form = {
                    sharing_patient_id: sharingPatientId,
                    patient_id: $scope.patient_id
                };

                staffService.addSharingPatient(form).then(function (data) {
                    if (data['success']) {
                        $scope.sharing_patients.push(data['sharing_patient']);
                        form.sharing_patient_id = '';

                        toaster.pop('success', 'Done', 'Added sharing patient successfully');
                    } else {
                        toaster.pop('error', 'Error', 'Added sharing patient failed!');
                    }
                });
            }

            function remove_sharing_patient(userId) {
                staffService.removeSharingPatient($scope.patient_id, userId)
                    .then(function (data) {
                        if (data['success']) {
                            $scope.sharing_patients.forEach((p, idx) => {
                                if (p.user.id == userId) {
                                    $scope.sharing_patients.splice(idx, 1);
                                }
                            });

                            toaster.pop('success', 'Done', 'Removed sharing patient successfully');
                        } else {
                            toaster.pop('error', 'Error', 'Removed sharing patient error!');
                        }
                    });
            }

            function isShared(result) {
                let isShared = false;
                $scope.sharing_patients.forEach((patient) => {
                    if (patient.id == result.id) {
                        isShared = true;
                    }
                });
                return isShared;
            }

            function findPatient(viewValue) {
                if (viewValue != '') {
                    return inrService.findPatient(viewValue).then(function (response) {
                        $scope.results = response.data.patients;
                    });
                } else {
                    $scope.results = [];
                }
                return $scope.results;
            }

            function permitted(user) {
                var permitted = true;
                if (user.id == $scope.patient.user.id) {
                    permitted = false;
                }

                angular.forEach($scope.sharing_patients, function (value, key) {
                    if (user.id == value.user.id) {
                        permitted = false;
                    }
                });
                return permitted;
            }
        });
    /* End of controller */


    angular.module('ManagerApp')
        .controller('ManageSharingProblemCtrl', function ($scope, $routeParams, ngDialog, problemService, sharedService,
                                                          patientService, $location, $anchorScroll, toaster) {

            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;

            var sharing_patient_id = $routeParams.sharing_patient_id;
            $scope.sharing_patient_id = sharing_patient_id;

            patientService.fetchActiveUser().then(function (data) {
                $scope.active_user = data['user_profile'];
            });

            patientService.getUserInfo($scope.sharing_patient_id).then(function (data) {
                $scope.sharing_patient = data['user_profile'];
            });

            problemService.fetchProblems($scope.patient_id).then(function (data) {
                $scope.problems = data['problems'];
            });

            problemService.fetchSharingProblems($scope.patient_id, $scope.sharing_patient_id).then(function (data) {
                $scope.sharing_problems = data['sharing_problems'];
                $scope.is_my_story_shared = data['is_my_story_shared'];
            });

            //sharedService.initHotkey($scope);

            $scope.inArray = function (array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value.id == item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            };

            $scope.changeSharingProblem = function (problem) {
                var is_existed = false;
                var index;
                angular.forEach($scope.sharing_problems, function (value, key2) {
                    if (value.id == problem.id) {
                        is_existed = true;
                        index = key2;
                    }
                });

                if (is_existed) {
                    $scope.sharing_problems.splice(index, 1);
                    problemService.removeSharingProblems($scope.patient_id, $scope.sharing_patient_id, problem.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Removed problem');
                    });
                } else {
                    $scope.sharing_problems.push(problem);

                    problemService.addSharingProblems($scope.patient_id, $scope.sharing_patient_id, problem.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Added problem');
                    });

                }
            };

            $scope.changeSharingMyStory = function () {
                patientService.changeSharingMyStory($scope.patient_id, $scope.sharing_patient_id).then(function (data) {
                    toaster.pop('success', 'Done', 'Changed sharing my story');
                });
            };
        });
    /* End of controller */


})();