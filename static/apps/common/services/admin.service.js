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

    angular.module('app.services')
        .service('adminService', function ($q, $cookies, $http, httpService) {
            return {
                csrf_token: csrf_token,
                fetchActiveUser: fetchActiveUser,
                getUsersList: getUsersList,
                getPendingRegistrationUsersList: getPendingRegistrationUsersList,
                getUserInfo: getUserInfo,
                approveUser: approveUser,
                updateBasicProfile: updateBasicProfile,
                updateProfile: updateProfile,
                updateEmail: updateEmail,
                updatePassword: updatePassword,
                addUser: addUser,
                getPatientPhysicians: getPatientPhysicians,
                getPhysicianData: getPhysicianData,
                getAssignedPhysicians: getAssignedPhysicians,
                assignMember: assignMember,
                unassignMember: unassignMember,
                getPatientsList: getPatientsList,
                getSharingPatients: getSharingPatients,
                addSharingPatient: addSharingPatient,
                removeSharingPatient: removeSharingPatient,
                fetchProblems: fetchProblems,
                fetchSharingProblems: fetchSharingProblems,
                removeSharingProblems: removeSharingProblems,
                addSharingProblems: addSharingProblems,
                updateActive: updateActive,
                updateDeceasedDate: updateDeceasedDate,
            };

            function csrf_token() {

                return $cookies.get('csrftoken');
            }

            function fetchActiveUser() {

                let params = {};
                let url = '/u/active/user/';

                return httpService.get(params, url);

            }

            function getUsersList(form) {
                let params = form;
                let url = '/project/admin/list/registered/users/';
                return httpService.get(params, url);
            }

            function getPendingRegistrationUsersList(form) {
                let params = form;
                let url = '/project/admin/list/unregistered/users/';
                return httpService.get(params, url);
            }

            function getUserInfo(user_id) {

                let params = {user_id: user_id};
                let url = `/project/admin/user/${user_id}/info/`;
                return httpService.get(params, url);

            }

            function approveUser(user) {

                let form = user;
                let url = '/project/admin/user/approve/';
                return httpService.post(form, url);

            }

            function updateBasicProfile(form) {
                let url = '/project/admin/user/update/basic/';
                return httpService.post(form, url);

            }

            function updateProfile(form, files) {


                let deferred = $q.defer();

                let uploadUrl = '/project/admin/user/update/profile/';

                let fd = new FormData();

                fd.append('csrfmiddlewaretoken', this.csrf_token());

                angular.forEach(form, function (value, key) {
                    fd.append(key, value);
                });

                angular.forEach(files, function (value, key) {
                    fd.append(key, value);
                });


                $http.post(uploadUrl, fd, {
                    transformRequest: angular.identity,

                    headers: {'Content-Type': undefined}
                })
                    .success(function (data) {
                        deferred.resolve(data);
                    })
                    .error(function (data) {
                        deferred.resolve(data);

                    });

                return deferred.promise;

            }

            function updateEmail(form) {
                let url = '/project/admin/user/update/email/';
                return httpService.post(form, url);
            }

            function updatePassword(form) {
                let url = '/project/admin/user/update/password/';
                return httpService.post(form, url);
            }

            function addUser(form) {
                let url = '/project/admin/user/create/';
                return httpService.post(form, url);
            }

            function getPatientPhysicians(params) {

                let url = '/project/admin/patient/physicians/';
                return httpService.get(params, url);

            }

            function getPhysicianData(params) {

                let url = '/project/admin/physician/data/';
                return httpService.get(params, url);
            }

            function getAssignedPhysicians(params) {
                let url = '/project/admin/assigned/physicians/';
                return httpService.get(params, url);
            }

            function assignMember(form) {

                let url = '/project/admin/physician/assign/member/';
                return httpService.post(form, url);
            }

            function unassignMember(form) {
                let url = '/project/admin/physician/unassign/member/';
                return httpService.post(form, url);
            }

            function getPatientsList() {
                let form = {};
                let url = '/u/patients/';
                return httpService.post(form, url);
            }

            function getSharingPatients(patient_id) {
                let form = {};
                let url = `/u/sharing_patients/${patient_id}`;
                return httpService.post(form, url);
            }

            function addSharingPatient(form) {
                let url = `/u/patient/add_sharing_patient/${form.patient_id}/${form.sharing_patient_id}`;
                return httpService.post(form, url);
            }

            function removeSharingPatient(patient_id, sharing_patient_id) {
                let form = {};
                let url = `/u/patient/remove_sharing_patient/${patient_id}/${sharing_patient_id}`;
                return httpService.post(form, url);
            }

            function fetchProblems(patient_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/getproblems`;
                return httpService.get(params, url);
            }

            function fetchSharingProblems(patient_id, sharing_patient_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${sharing_patient_id}/get_sharing_problems`;
                return httpService.get(params, url);
            }

            function removeSharingProblems(patient_id, sharing_patient_id, problem_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${sharing_patient_id}/${problem_id}/remove_sharing_problems`;
                return httpService.post(params, url);
            }

            function addSharingProblems(patient_id, sharing_patient_id, problem_id) {
                let params = {};
                let url = `/p/problem/${patient_id}/${sharing_patient_id}/${problem_id}/add_sharing_problems`;
                return httpService.post(params, url);
            }

            function updateActive(form) {
                let url = '/project/admin/user/update/active/';
                return httpService.post(form, url);
            }

            function updateDeceasedDate(form) {
                let url = '/project/admin/user/update/deceased_date/';
                return httpService.post(form, url);
            }
        });

})();