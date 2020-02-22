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
        .controller('EditUserCtrl', function ($scope, $routeParams, ngDialog, sharedService, patientService, $location, $anchorScroll, toaster) {

            // $scope.user_id = $('#patient_id').val();
            $scope.staff_roles = ['nurse', 'secretary', 'mid-level'];
            $scope.insurance = {}; // Patient insurance form

            $scope.updateImage = updateImage;
            $scope.update_basic_profile = update_basic_profile;
            $scope.update_profile = update_profile;
            $scope.update_email = update_email;
            $scope.update_patient_password = update_patient_password;
            $scope.navigate = navigate;
            $scope.submitInsurance = submitInsurance;

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
                $scope.insurance.medicare = $scope.patient_info.insurance_medicare;
                $scope.insurance.note = $scope.patient_info.insurance_note;
                $scope.files = {};
                setTimeout(() => {
                    navigate($routeParams.section);
                }, 500);
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
                    } else {
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

            function submitInsurance() {
                patientService.updateMedicare($scope.patient_id, $scope.insurance);
            }

        });
    /* End of controller */


})();