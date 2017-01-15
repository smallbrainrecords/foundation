(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('ManageSharingPatientCtrl', function ($scope, $routeParams, ngDialog, sharedService,
                                                          patientService, $location, $anchorScroll, toaster) {

            $scope.init = function () {

                var patient_id = $('#patient_id').val();
                $scope.patient_id = patient_id;

                $scope.assign_patient_form = {};

                patientService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });

                patientService.getPatientsList().then(function (data) {
                    $scope.patients_list = data['patients_list'];
                });

                patientService.getSharingPatients($scope.patient_id).then(function (data) {
                    $scope.sharing_patients = data['sharing_patients'];
                });
                //sharedService.initHotkey($scope);

            };

            $scope.add_sharing_patient = function (form) {
                form.patient_id = $scope.patient_id;

                patientService.addSharingPatient(form).then(function (data) {
                    if (data['success'] == true) {
                        $scope.sharing_patients.push(data['sharing_patient']);
                        form.sharing_patient_id = '';

                        toaster.pop('success', 'Done', 'Added sharing patient successfully');
                    } else {
                        toaster.pop('error', 'Error', 'Something error! Please try again!');
                    }
                });
            };

            $scope.remove_sharing_patient = function (p) {
                patientService.removeSharingPatient($scope.patient_id, p.user.id).then(function (data) {
                    if (data['success'] == true) {
                        var index = $scope.sharing_patients.indexOf(p);
                        $scope.sharing_patients.splice(index, 1);

                        toaster.pop('success', 'Done', 'Removed sharing patient successfully');
                    } else {
                        toaster.pop('error', 'Error', 'Something error! Please try again!');
                    }
                });
            };

            $scope.permitted = function (p) {
                var permitted = true;
                if (p.user.id == $scope.active_user.user.id) {
                    permitted = false;
                }

                angular.forEach($scope.sharing_patients, function (value, key) {
                    if (p.user.id == value.user.id) {
                        permitted = false;
                    }
                });

                return permitted;

            };

            $scope.init();

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