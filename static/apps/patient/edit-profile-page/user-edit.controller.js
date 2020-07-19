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
        .controller('EditUserCtrl', function ($scope, $routeParams, patientService, $location, $anchorScroll, toaster, DATEPICKER_OPTS, moment) {

            $scope.DATEPICKER_OPTS = DATEPICKER_OPTS;
            $scope.dateFormat = 'MM/dd/yyyy';
            $scope.datePickerOpened = false;

            $scope.profileInfoFormModel = {
                dateOfBirth: new Date(),
                phoneNumber: "",
                sex: "",
                summary: ""
            };

            $scope.insuranceForm = {
                medicare: "",
                note: ""
            };
            $scope.old_password = "";
            $scope.password = "";
            $scope.repassword = "";

            $scope.navigate = navigate;
            $scope.updateBasicProfile = updateBasicProfile;
            $scope.updateProfile = updateProfile;
            $scope.updateImage = updateImage;
            $scope.updateEmail = updateEmail;
            $scope.updatePatientPassword = updatePatientPassword;
            $scope.submitInsurance = submitInsurance;

            init();

            function convertAPItoModelForm() {
                $scope.profileInfoFormModel.dateOfBirth = moment($scope.patient_info.date_of_birth, "MM/DD/YYYY").toDate();
                $scope.profileInfoFormModel.phoneNumber = $scope.patient_info.phone_number;
                $scope.profileInfoFormModel.sex = $scope.patient_info.sex;
                $scope.profileInfoFormModel.summary = $scope.patient_info.summary;
            }

            function init() {
                patientService.fetchPatientInfo($scope.patient_id)
                    .then((response) => {
                        let data = response.data;
                        $scope.sharing_patients = data['sharing_patients'];
                        $scope.shared_patients = data['shared_patients'];
                    });

                // DAO -> DTO
                convertAPItoModelForm();

                $scope.insuranceForm.medicare = $scope.patient_info.insurance_medicare;
                $scope.insuranceForm.note = $scope.patient_info.insurance_note;

                $scope.files = {};

                setTimeout(() => {
                    navigate($routeParams.section);
                }, 1000);
            }

            function navigate(l) {
                $location.hash(l);
                $anchorScroll();
            }

            function updateBasicProfile() {

                let form = {};

                form.user_id = $scope.patient_id;
                form.first_name = $scope.patient_info.user.first_name;
                form.last_name = $scope.patient_info.user.last_name;

                patientService.updateBasicProfile(form).then(response => {
                    let data = response.data;

                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Patient updated!');
                    } else if (!data['success']) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    }
                });
            }

            function updateProfile() {

                let form = {
                    user_id: $scope.patient_id,
                    role: $scope.patient_info.role,
                    date_of_birth: moment($scope.profileInfoFormModel.dateOfBirth).format('MM/DD/YYYY'),
                    phone_number: $scope.profileInfoFormModel.phoneNumber,
                    sex: $scope.profileInfoFormModel.sex,
                    summary: $scope.profileInfoFormModel.summary,
                };
                let files = $scope.files;

                patientService.updateProfile(form, files)
                    .then(function (response) {
                        let data = response.data;
                        if (data['success']) {
                            toaster.pop('success', 'Done', 'Patient updated!');
                            $scope.patient_info = data['info'];
                            convertAPItoModelForm();
                        } else if (!data['success']) {
                            toaster.pop('error', 'Error', 'Please fill valid data');
                        }
                    });
            }

            function updateEmail() {

                let form = {};

                form.user_id = $scope.patient_id;
                form.email = $scope.patient_info.user.email;

                patientService.updateEmail(form).then(response => {
                    let data = response.data;

                    if (data.success) {
                        toaster.pop('success', 'Done', 'Patient updated!');

                    } else if (!data.success) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    }
                });

            }

            function updatePatientPassword() {

                if ($scope.old_password === undefined || $scope.password === undefined || $scope.repassword === undefined) {
                    toaster.pop('error', 'Error', 'Please enter password');
                    return false;
                }
                if ($scope.password !== $scope.repassword) {
                    toaster.pop('error', 'Error', 'Password must match');
                    return false;
                }
                let form = {
                    'patient_id': $scope.patient_id,
                    'old_password': $scope.old_password,
                    'password': $scope.password,
                    'repassword': $scope.repassword,
                };

                patientService.updatePatientPassword(form).then(response => {
                    let data = response.data;
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

            function updateImage() {
                let form = {};
                form.user_id = $scope.patient_id;
                let files = $scope.files;


                patientService.updateProfile(form, files)
                    .then(response => {
                        let data = response.data;
                        if (data.success) {
                            toaster.pop('success', 'Done', 'Updated');
                        } else {
                            toaster.pop('error', 'Error', 'Update failed');
                        }
                    });
            }

            function submitInsurance() {
                patientService.updateMedicare($scope.patient_id, $scope.insuranceForm).then(response => {
                    let data = response.data;
                    if (data.success) {
                        toaster.pop('success', 'Done', 'Updated');
                    } else {
                        toaster.pop('error', 'Error', 'Update failed');
                    }
                });
            }

        });
    /* End of controller */
})();
