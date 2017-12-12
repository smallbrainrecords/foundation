(function () {
    "use strict";

    angular.module('inr')
        .directive('inrBfdi', inrBfdi);

    inrBfdi.$inject = ["toaster", "inrService", "$http"];

    function inrBfdi(toaster, inrService, $http) {
        return {
            restrict: 'E',
            templateUrl: '/static/apps/inr/inr-bfdi.template.html',
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