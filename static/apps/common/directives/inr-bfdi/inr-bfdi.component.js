/*
 * Copyright (c) Small Brain Records 2014-2020. Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
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
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */
(function () {
    "use strict";

    angular.module('inr')
        .directive('inrBfdi', inrBfdi);

    inrBfdi.$inject = ["toaster", "inrService", "$http"];

    function inrBfdi(toaster, inrService, $http) {
        return {
            restrict: 'E',
            templateUrl: '/static/apps/common/directives/inr-bfdi/inr-bfdi.template.html',
            scope: true,
            link: linkFn
        };

        function linkFn(scope, element, attr, model) {
            scope.inr = {inr_value: null};

            scope.loadingPatients = true;
            scope.isOpenned = true;
            scope.patientName = "";

            scope.addINR = addINR;
            scope.findPatient = findPatient;
            scope.typeaheadOnSelect = typeaheadOnSelect;

            // Function implementation
            function typeaheadOnSelect($item, $model, $label, $event) {
                $event.stopPropagation();
                $event.preventDefault();
            }

            function addINR(patient) {

                inrService.addINR(patient.id, scope.inr).then(addINRSuccess, addINRError);

                function addINRSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Add new INR success');
                    } else {
                        toaster.pop('error', 'Error', 'Patient does not have INR data type');
                    }
                }

                function addINRError() {
                    toaster.pop('error', 'Error', 'Something wrong we fixed this ASAP');
                }
            }

            /**
             *
             * @param viewValue
             */
            function findPatient(viewValue) {
                if (viewValue != '') {
                    return inrService.findPatient(viewValue).then(function (response) {
                        scope.results = response.data.patients;
                    });
                } else {
                    scope.results = [];
                }
                return scope.results;
            }
        }
    }

})();