(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('EditUserCtrl', function ($scope, $routeParams, ngDialog, sharedService, patientService, $location, $anchorScroll, toaster) {

            // $scope.user_id = $('#patient_id').val();
            $scope.staff_roles = ['nurse', 'secretary', 'mid-level'];

            $scope.updateImage = updateImage;
            $scope.update_basic_profile = update_basic_profile;
            $scope.update_profile = update_profile;
            $scope.update_email = update_email;
            $scope.update_patient_password = update_patient_password;
            $scope.navigate = navigate;

            init();

            function init() {

                // patientService.fetchActiveUser().then(function (data) {
                //     $scope.active_user = data['user_profile'];
                // });

                patientService.fetchPatientInfo($scope.patient_id).then(function (data) {
                    // $scope.patient_info = data['info'];
                    $scope.sharing_patients = data['sharing_patients'];
                    $scope.shared_patients = data['shared_patients'];
                });

                $scope.files = {};
            }

            function update_basic_profile() {

                let form = {};

                form.user_id = $scope.patient_id;
                form.first_name = $scope.patient_info.user.first_name;
                form.last_name = $scope.patient_info.user.last_name;

                patientService.updateBasicProfile(form).then(function (data) {

                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Patient updated!');
                    } else if (!data['success']) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            }

            function update_profile() {

                let form = {};
                form.user_id = $scope.patient_id;
                form.phone_number = $scope.patient_info.phone_number;
                form.sex = $scope.patient_info.sex;
                form.role = $scope.patient_info.role;
                form.summary = $scope.patient_info.summary;
                form.date_of_birth = $scope.patient_info.date_of_birth;

                let files = $scope.files;

                patientService.updateProfile(form, files).then(function (data) {

                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Patient updated!');
                        $scope.patient_info = data['info'];
                    } else if (!data['success']) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }

                });

            }

            function update_email() {

                let form = {};

                form.user_id = $scope.patient_id;
                form.email = $scope.patient_info.user.email;

                patientService.updateEmail(form).then(function (data) {

                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Patient updated!');

                    } else if (!data['success']) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }

                });

            }

            // change patient password
            function update_patient_password() {

                if ($scope.old_password == undefined || $scope.password == undefined || $scope.repassword == undefined) {
                    toaster.pop('error', 'Error', 'Please enter password');
                    return false;
                }
                if ($scope.password != $scope.repassword) {
                    toaster.pop('error', 'Error', 'Password must match');
                    return false;
                }
                let form = {
                    'patient_id': $scope.patient_id,
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

            }

            function navigate(l) {
                /* Replace by directive */
                $("html, body").animate({scrollTop: $('#' + l).offset().top - 100}, 500);
            }

            function updateImage() {
                let form = {};
                form.user_id = $scope.patient_id;
                let files = $scope.files;


                patientService.updateProfile(form, files)
                    .then(function (data) {
                        if (data['success']) {
                            toaster.pop('success', 'Done', 'Updated');
                        } else {
                            toaster.pop('error', 'Error', 'Update failed');
                        }
                    }, function () {
                        toaster.pop('error', 'Error', 'Something went wrong! We fix ASAP');
                    });
            }

        });
    /* End of controller */


})();
