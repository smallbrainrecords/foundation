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
            var now = new Date();
            scope.inr = {
                date_measured: now,
                inr_value: null, // This is nurse entry
                next_inr: new Date(now.getFullYear(), now.getMonth() + 1, now.getDate())
            };

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
                scope.inr.current_dose = patient.current_dose;
                scope.inr.new_dosage = patient.new_dosage;

                inrService.addINR(patient.id, scope.inr).then(addINRSuccess, addINRError);

                function addINRSuccess(response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Add new INR success');
                    } else {
                        toaster.pop('error', 'Error', 'Add INR failed');
                    }
                }

                function addINRError() {
                    toaster.pop('error', 'Error', 'Add INR failed');
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