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
    "use strict";

    angular.module('medication-component', [])
        .component('medicationSearch', {
            bindings: {
                searchTerm: '<',
                onUpdate: '&'
            },
            templateUrl: "/static/apps/common/directives/medication/medication-search.html",
            controller: medicationSearchController
        });

    /**
     * Inject dependencies
     * @type {[*]}
     */
    medicationSearchController.$inject = ['medicationService'];


    /**
     * Reusable medication search box Add new or update existing(depend on update callback)
     * Input: Initial search string (default: empty)
     * Output: Update or Create callback
     *
     * @param medicationService
     */
    function medicationSearchController(medicationService) {
        // Temporary solution for this (controllerAs syntax)
        var ctrl = this;

        // PROPERTIES

        ctrl.medicationTerms = []; // Medication terms result set
        ctrl.new_medication = {set: false}; // Medication are selected in result set
        ctrl.setMedication = setMedication;
        ctrl.unsetNewMedication = unsetNewMedication;
        ctrl.termChanged = termChanged;

        /**
         * Constructor
         */
        ctrl.$onInit = function () {

            if (ctrl.searchTerm) {
                medicationService.listTerms(ctrl.searchTerm).then(listTermSuccessCallback);
            }
        };


        // METHOD DEFINITION

        /**
         * List term callback
         * @param data
         */
        function listTermSuccessCallback(response) {
            let data = response.data;
            ctrl.medicationTerms = data;
        }

        /**
         * TODO: Bad implementation, should be refactored
         * Set new medication
         * @param medication
         */
        function setMedication(medication) {
            ctrl.new_medication.set = true;
            ctrl.new_medication.name = medication.name;
            ctrl.new_medication.concept_id = medication.concept_id;
            ctrl.new_medication.search_str = ctrl.searchTerm;
        }

        /**
         * Unset medication
         * TODO: Bad implementation, should be refactored
         */
        function unsetNewMedication() {
            ctrl.new_medication.set = false;
        }

        /**
         * Change term handler
         */
        function termChanged() {
            if (ctrl.searchTerm.length >= 3) {
                medicationService.listTerms(ctrl.searchTerm).then(listTermSuccessCallback);
            }
        }
    }
})();