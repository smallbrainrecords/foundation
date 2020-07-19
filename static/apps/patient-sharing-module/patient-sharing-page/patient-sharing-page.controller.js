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
    angular.module('app.patientSharingModule')
        .controller('PatientSharingCtrl', PatientSharingCtrl);
    PatientSharingCtrl.$inject = ['$scope', '$routeParams', 'staffService', 'toaster', 'inrService'];

    function PatientSharingCtrl($scope, $routeParams, staffService, toaster, inrService) {

        $scope.patientId = $routeParams.patientId;
        $scope.patientName = '';
        $scope.assignPatientForm = {};
        $scope.sharingPatients = [];

        $scope.findPatient = findPatient;
        $scope.addSharingPatient = addSharingPatient;
        $scope.removeSharingPatient = removeSharingPatient;
        $scope.permitted = permitted;
        $scope.isShared = isShared;

        init();

        function init() {
            staffService.getUserInfo($scope.patientId).then((response) => {
                let data = response.data;
                $scope.patient = data['user_profile'];
            });

            staffService.getSharingPatients($scope.patientId).then((response) => {
                let data = response.data;
                $scope.sharingPatients = data['sharing_patients'];
            });

        }

        function findPatient(viewValue) {
            if (viewValue !== '') {
                return inrService.findPatient(viewValue).then(function (response) {
                    let data = response.data;
                    $scope.results = data.patients;
                });
            } else {
                $scope.results = [];
            }
            return $scope.results;
        }

        function addSharingPatient(sharingPatientId) {
            let form = {
                sharing_patient_id: sharingPatientId,
                patient_id: $scope.patientId
            };

            staffService.addSharingPatient(form).then(function (response) {
                let data = response.data;
                if (data['success']) {
                    $scope.sharingPatients.push(data['sharing_patient']);
                    form.sharing_patient_id = '';

                    toaster.pop('success', 'Done', 'Added sharing patient successfully');
                } else {
                    toaster.pop('error', 'Error', 'Added sharing patient failed!');
                }
            });
        }

        function removeSharingPatient(userId) {
            staffService.removeSharingPatient($scope.patientId, userId)
                .then(function (response) {
                    let data = response.data;
                    if (data['success']) {
                        $scope.sharingPatients.forEach((p, idx) => {
                            if (p.user.id === userId) {
                                $scope.sharingPatients.splice(idx, 1);
                            }
                        });

                        toaster.pop('success', 'Done', 'Removed sharing patient successfully');
                    } else {
                        toaster.pop('error', 'Error', 'Removed sharing patient error!');
                    }
                });
        }

        /**
         * TODO: Nested for each 2 level
         * @param result
         * @return {boolean}
         */
        function isShared(result) {
            let isShared = false;
            $scope.sharingPatients.forEach((patient) => {
                if (patient.id === result.id) {
                    isShared = true;
                }
            });
            return isShared;
        }

        /**
         * TODO: Nested for each
         * @param user
         * @return {boolean}
         */
        function permitted(user) {
            let permitted = true;
            if (user.id === $scope.patient.user.id) {
                permitted = false;
            }

            angular.forEach($scope.sharingPatients, function (value) {
                if (user.id === value.user.id) {
                    permitted = false;
                }
            });
          return permitted;
        }
    }
    /* End of controller */
})();