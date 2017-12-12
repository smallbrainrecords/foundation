(function () {
    "use strict";

    angular.module('medication-component', [])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .component('medicationSearch', {
            bindings: {
                searchTerm: '<',
                onUpdate: '&'
            },
            templateUrl: "/static/apps/medication/medication-search.html",
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
        function listTermSuccessCallback(data) {
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