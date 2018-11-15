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


    angular.module('AdminApp')
        .controller('EditUserCtrl', function ($scope, $routeParams, ngDialog, adminService, $location, $anchorScroll, toaster) {

            $scope.staff_roles = ['nurse', 'secretary', 'mid-level'];
            $scope.update_basic_profile = update_basic_profile;
            $scope.update_profile = update_profile;
            $scope.update_email = update_email;
            $scope.update_password = update_password;
            $scope.navigate = navigate;
            $scope.show_physician_assigned = show_physician_assigned;
            $scope.assign_physician = assign_physician;
            $scope.unassign_physician = unassign_physician;
            $scope.assign_member = assign_member;
            $scope.unassign_member = unassign_member;
            $scope.remove_item_by_id = remove_item_by_id;
            $scope.update_active = update_active;
            $scope.update_deceased_date = update_deceased_date;
            $scope.updateImage = updateImage;

            init();

            function init() {

                $scope.user_id = $routeParams['userId'];

                /* Needed for form initialization */
                $scope.assign_patient_form = {'member_type': 'patient'};
                $scope.assign_nurse_form = {'member_type': 'nurse'};
                $scope.assign_mid_level_form = {'member_type': 'mid-level'};
                $scope.assign_secretary_form = {'member_type': 'secretary'};

                $scope.assign_physician_form = {};

                adminService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });


                adminService.getUserInfo($scope.user_id).then(function (data) {

                    $scope.user_profile = data['user_profile'];

                    if ($scope.user_profile.role == 'physician') {

                        // physicians
                        var form = {'physician_id': $scope.user_id};

                        adminService.getPhysicianData(form).then(function (data) {

                            $scope.team = data['team'];
                            $scope.patients = data['patients'];

                            $scope.unassigned_patients = data['unassigned_patients'];
                            $scope.nurses_list = data['nurses_list'];
                            $scope.secretaries_list = data['secretaries_list'];
                            $scope.mid_level_staffs_list = data['mid_level_staffs_list'];
                        });

                    } else {
                        // patients , nurses, mid-level, secretary
                        var form = {'user_id': $scope.user_id};
                        form.member_type = $scope.user_profile.role;

                        adminService.getAssignedPhysicians(form).then(function (data) {
                            $scope.assigned_physicians = data['physicians'];
                            $scope.unassigned_physicians = data['unassigned_physicians'];
                        });
                    }


                });


                $scope.files = {};
                $scope.password_form = {};

            }


            function update_basic_profile() {

                var form = {};

                form.user_id = $scope.user_id;
                form.first_name = $scope.user_profile.user.first_name;
                form.last_name = $scope.user_profile.user.last_name;

                adminService.updateBasicProfile(form).then(function (data) {
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Updated');
                    } else {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    }
                }, function () {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });

            }

            function update_profile() {

                var form = {};
                form.user_id = $scope.user_id;
                form.phone_number = $scope.user_profile.phone_number;
                form.sex = $scope.user_profile.sex;
                form.role = $scope.user_profile.role;
                form.summary = $scope.user_profile.summary;
                form.date_of_birth = $scope.user_profile.date_of_birth;

                var files = $scope.files;

                adminService.updateProfile(form, files)
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

            function updateImage() {
                var form = {};
                form.user_id = $scope.user_id;
                var files = $scope.files;


                adminService.updateProfile(form, files)
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

            function update_email() {

                var form = {};

                form.user_id = $scope.user_id;
                form.email = $scope.user_profile.user.email;


                /* Files */

                adminService.updateEmail(form)
                    .then(function (data) {
                        if (data['success']) {
                            toaster.pop('success', 'Done', 'Updated');
                        } else {
                            toaster.pop('error', 'Error', 'Please fill valid data');
                        }
                    }, function () {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    });
            }

            function update_password() {

                var form = {};

                form.user_id = $scope.user_id;
                form.new_password = $scope.password_form.new_password;
                form.verify_password = $scope.password_form.verify_password;

                /* Files */

                adminService.updatePassword(form).then(function (data) {
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Updated');
                    } else {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    }
                }, function () {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });

            }

            function navigate(l) {
                /* Replace by directive */

                $("html, body").animate({scrollTop: $('#' + l).offset().top - 100}, 500);
            }

            function show_physician_assigned(role) {

                var permitted = ['patient', 'nurse', 'secretary', 'mid-level'];
                return permitted.indexOf(role) > -1;
            }

            function assign_physician(form) {
                form.user_id = $scope.user_id;
                form.member_type = $scope.user_profile.role;

                adminService.assignMember(form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Assigned Physician');
                        var new_physician = $scope.remove_item_by_id($scope.unassigned_physicians, form.physician_id);
                        $scope.assigned_physicians.push(new_physician);

                    } else {
                        toaster.pop('error', 'Error', 'Failed');
                    }
                }, function () {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });

            }

            function unassign_physician(physician_id) {
                var form = {};
                form.physician_id = physician_id;
                form.user_id = $scope.user_id;
                form.member_type = $scope.user_profile.role;

                adminService.unassignMember(form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Unassigned Physician');

                        var old_physician = $scope.remove_item_by_id($scope.assigned_physicians, form.physician_id);
                        $scope.unassigned_physicians.push(old_physician);
                    }
                });

            }

            function assign_member(form) {
                /* Physician specific */
                form.physician_id = $scope.user_id;

                console.log(form);

                adminService.assignMember(form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Added member');

                        if (form.member_type == 'patient') {
                            var new_member = $scope.remove_item_by_id($scope.unassigned_patients, form.user_id);
                            $scope.patients.push(new_member);
                        } else if (form.member_type == 'nurse') {
                            var new_member = $scope.remove_item_by_id($scope.nurses_list, form.user_id);
                            $scope.team.nurses.push(new_member);
                        } else if (form.member_type == 'secretary') {
                            var new_member = $scope.remove_item_by_id($scope.secretaries_list, form.user_id);
                            $scope.team.secretaries.push(new_member);
                        } else if (form.member_type == 'mid-level') {
                            var new_member = $scope.remove_item_by_id($scope.mid_level_staffs_list, form.user_id);
                            $scope.team.mid_level_staffs.push(new_member);
                        }

                        form.user_id = '';
                    }

                });

            }

            function unassign_member(member, member_type) {
                /* Physician specific */
                var form = {};
                form.user_id = member.user.id;
                form.member_type = member_type;
                form.physician_id = $scope.user_id;

                adminService.unassignMember(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Unassigned member');

                        if (form.member_type == 'patient') {
                            var user_profile = $scope.remove_item_by_id($scope.patients, form.user_id);
                            $scope.unassigned_patients.push(user_profile);
                        } else if (form.member_type == 'nurse') {
                            var user_profile = $scope.remove_item_by_id($scope.team.nurses, form.user_id);
                            $scope.nurses_list.push(user_profile);
                        } else if (form.member_type == 'secretary') {
                            var user_profile = $scope.remove_item_by_id($scope.team.secretaries, form.user_id);
                            $scope.secretaries_list.push(user_profile);
                        } else if (form.member_type == 'mid-level') {
                            var user_profile = $scope.remove_item_by_id($scope.team.mid_level_staffs, form.user_id);
                            $scope.mid_level_staffs_list.push(user_profile);
                        }
                    }

                });

            }

            function remove_item_by_id(items, item_id) {
                var target = null;
                var target_value = null;
                angular.forEach(items, function (value, key) {
                    console.log(value, key);
                    if (value.user.id == item_id) {
                        target = key;
                        target_value = value;
                    }
                });

                if (target != null) {
                    items.splice(target, 1);
                }
                return target_value;
            }

            function update_active() {

                var form = {};

                form.user_id = $scope.user_id;
                form.is_active = $scope.user_profile.user.is_active;
                if (form.is_active)
                    $scope.user_profile.active_reason = '';
                form.active_reason = $scope.user_profile.active_reason;

                adminService.updateActive(form).then(function (data) {
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Updated');
                    } else {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    }
                }, function () {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });

            }

            function update_deceased_date() {

                var form = {};

                form.user_id = $scope.user_id;
                form.deceased_date = $scope.user_profile.deceased_date;

                if (form.deceased_date == '') {

                } else if (!moment(form.deceased_date, "MM/DD/YYYY", true).isValid()) {
                    toaster.pop('error', 'Error', 'Please enter a valid date!');
                    $scope.user_profile.user.is_active = false;
                    return false;
                }

                adminService.updateDeceasedDate(form).then(function (data) {
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Updated');
                    } else {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    }
                }, function () {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });
            }
        });
    /* End of controller */


})();