(function () {
    'use strict';
    angular.module('AdminApp')
        .controller('ManageSharingCtrl', function ($scope, $routeParams, ngDialog, adminService, $location, $anchorScroll, toaster) {
            adminService.getPatientsList().then(function (data) {
                $scope.patients_list = data['patients_list'];
            });
        });
    /* End of controller */
    angular.module('AdminApp')
        .controller('ManageSharingPatientCtrl', function ($scope, $routeParams, ngDialog,
                                                          adminService, $location, $anchorScroll, toaster) {
            $scope.add_sharing_patient = add_sharing_patient;
            $scope.remove_sharing_patient = remove_sharing_patient;
            $scope.permitted = permitted;

            init();

            function init() {
                $scope.patient_id = $routeParams['patientId'];
                $scope.assign_patient_form = {};
                adminService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });
                adminService.getUserInfo($scope.patient_id).then(function (data) {
                    $scope.patient = data['user_profile'];
                });
                adminService.getPatientsList().then(function (data) {
                    $scope.patients_list = data['patients_list'];
                });
                adminService.getSharingPatients($scope.patient_id).then(function (data) {
                    $scope.sharing_patients = data['sharing_patients'];
                });
            }

            function add_sharing_patient(form) {
                form.patient_id = $scope.patient_id;
                adminService.addSharingPatient(form).then(function (data) {
                    if (data['success'] == true) {
                        $scope.sharing_patients.push(data['sharing_patient']);
                        form.sharing_patient_id = '';
                        toaster.pop('success', 'Done', 'Added sharing patient successfully');
                    } else {
                        toaster.pop('error', 'Error', 'Something error! Please try again!');
                    }
                });
            }

            function remove_sharing_patient(p) {
                adminService.removeSharingPatient($scope.patient_id, p.user.id).then(function (data) {
                    if (data['success'] == true) {
                        var index = $scope.sharing_patients.indexOf(p);
                        $scope.sharing_patients.splice(index, 1);
                        toaster.pop('success', 'Done', 'Removed sharing patient successfully');
                    } else {
                        toaster.pop('error', 'Error', 'Something error! Please try again!');
                    }
                });
            }

            function permitted(p) {
                var permitted = true;
                if (p.user.id == $scope.patient.user.id) {
                    permitted = false;
                }
                angular.forEach($scope.sharing_patients, function (value, key) {
                    if (p.user.id == value.user.id) {
                        permitted = false;
                    }
                });
                return permitted;
            }
        });
    /* End of controller */
    angular.module('AdminApp')
        .controller('ManageSharingProblemCtrl', function ($scope, $routeParams, ngDialog,
                                                          adminService, $location, $anchorScroll, toaster) {
            $scope.patient_id = $routeParams['patientId'];
            $scope.sharing_patient_id = $routeParams.sharing_patient_id;
            $scope.inArray = inArray;
            $scope.changeSharingProblem = changeSharingProblem;
            init();
            function init() {
                adminService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });
                adminService.getUserInfo($scope.patient_id).then(function (data) {
                    $scope.shared_patient = data['user_profile'];
                });
                adminService.getUserInfo($scope.sharing_patient_id).then(function (data) {
                    $scope.sharing_patient = data['user_profile'];
                });
                adminService.fetchProblems($scope.patient_id).then(function (data) {
                    $scope.problems = data['problems'];
                });
                adminService.fetchSharingProblems($scope.patient_id, $scope.sharing_patient_id).then(function (data) {
                    $scope.sharing_problems = data['sharing_problems'];
                });
            }

            function inArray(array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value.id == item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            }

            function changeSharingProblem(problem) {
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
                    adminService.removeSharingProblems($scope.patient_id, $scope.sharing_patient_id, problem.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Removed problem');
                    });
                } else {
                    $scope.sharing_problems.push(problem);
                    adminService.addSharingProblems($scope.patient_id, $scope.sharing_patient_id, problem.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Added problem');
                    });
                }
            }
        });
    /* End of controller */
})();