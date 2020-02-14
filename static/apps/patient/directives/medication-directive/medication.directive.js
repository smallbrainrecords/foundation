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
var medication = angular.module('medication', []).config(function ($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});

medication.directive('medication', ['CollapseService', 'toaster', '$location', '$timeout', 'prompt', 'medicationService', medicationDirective]);

function medicationDirective(CollapseService, toaster, $location, $timeout, prompt, medicationService) {

    return {
        restrict: 'E',
        templateUrl: '/static/apps/patient/directives/medication-directive/medication.html',
        scope: true,
        link: function (scope, element, attr, model) {
            scope.medications = scope.$eval(attr.ngModel);
            scope.medication_terms = [];
            scope.manual_medication = {};
            scope.new_medication = {set: false};

            scope.$watch('manual_medication.name', function (newVal, oldVal) {
                if (newVal == undefined) {
                    return false;
                }

                scope.unset_new_medication();

                if (newVal.length > 2) {
                    medicationService.listTerms(newVal).then(function (data) {
                        scope.medication_terms = data;
                    });
                } else {
                    scope.medication_terms = [];
                }
            });

            scope.unset_new_medication = function () {
                scope.new_medication.set = false;
            };

            scope.set_new_medication = function (medication) {
                scope.new_medication.set = true;
                scope.new_medication.name = medication.name;
                scope.new_medication.concept_id = medication.concept_id;
            };


            scope.add_medication = function (form) {
                // Preventing adding medication with empty name
                if (form.name == '')
                    return;

                form.search_str = scope.manual_medication.name;
                form.patient_id = scope.patient_id;
                medicationService.addMedication(form).then(function (data) {
                    if (data.success) {
                        toaster.pop('success', 'Done', 'Added medication!');
                        scope.medications.push(data['medication']);
                        form.name = '';
                        scope.unset_new_medication();
                        // Reset medication search terms after added to item
                        scope.manual_medication = {};
                        scope.medication_terms = [];
                    } else {
                        toaster.pop('error', 'Error', 'Medication name cannot empty');
                    }
                });
            };

            scope.open_medication = function (medication) {
                $location.url('/medication/' + medication.id);
            };
        }
    }

}
