(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('EditUserCtrl', function ($scope, $routeParams, ngDialog, sharedService,
                                              patientService, $location, $anchorScroll, toaster) {

            $scope.staff_roles = ['nurse', 'secretary', 'mid-level'];

            $scope.init = function () {

                $scope.user_id = $('#patient_id').val();

                patientService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });

                patientService.fetchPatientInfo($scope.user_id).then(function (data) {
                    $scope.user_profile = data['info'];
                    $scope.sharing_patients = data['sharing_patients'];
                    $scope.shared_patients = data['shared_patients'];
                });


                $scope.files = {};
                sharedService.initHotkey($scope);
            };


            $scope.update_basic_profile = function () {

                var form = {};

                form.user_id = $scope.user_id;
                form.first_name = $scope.user_profile.user.first_name;
                form.last_name = $scope.user_profile.user.last_name;

                patientService.updateBasicProfile(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Patient updated!');
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            };

            $scope.update_profile = function () {

                var form = {};
                form.user_id = $scope.user_id;
                form.phone_number = $scope.user_profile.phone_number;
                form.sex = $scope.user_profile.sex;
                form.role = $scope.user_profile.role;
                form.summary = $scope.user_profile.summary;
                form.date_of_birth = $scope.user_profile.date_of_birth;

                var files = $scope.files;

                patientService.updateProfile(form, files).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Patient updated!');
                        $scope.user_profile = data['info'];
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }

                });

            };


            $scope.update_email = function () {

                var form = {};

                form.user_id = $scope.user_id;
                form.email = $scope.user_profile.user.email;

                patientService.updateEmail(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Patient updated!');

                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }

                });

            };


            // change patient password
            $scope.update_patient_password = function () {

                if ($scope.old_password == undefined || $scope.password == undefined || $scope.repassword == undefined) {
                    toaster.pop('error', 'Error', 'Please enter password');
                    return false;
                }
                if ($scope.password != $scope.repassword) {
                    toaster.pop('error', 'Error', 'Password must match');
                    return false;
                }
                var form = {
                    'patient_id': $scope.user_id,
                    'old_password': $scope.old_password,
                    'password': $scope.password,
                    'repassword': $scope.repassword,
                };

                patientService.updatePatientPassword(form).then(function (data) {
                    if (data.success) {
                        toaster.pop('success', 'Done', 'Patient password updated!');
                        $scope.old_password = null;
                        $scope.password = null;
                        $scope.repassword = null;
                    }
                    else {
                        toaster.pop('error', 'Error', data.message);
                    }
                });

            };


            $scope.navigate = function (l) {
                /* Replace by directive */

                $("html, body").animate({scrollTop: $('#' + l).offset().top - 100}, 500);
            };


            $scope.init();

        });
    /* End of controller */


})();
