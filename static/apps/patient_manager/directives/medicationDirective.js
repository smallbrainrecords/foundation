var medication = angular.module('medication', []);

medication.directive('medication', ['CollapseService', 'toaster', '$location', '$timeout', 'prompt', 'medicationService', medicationDirective]);

function medicationDirective(CollapseService, toaster, $location, $timeout, prompt, medicationService) {

    return {
        restrict: 'E',
        templateUrl: '/static/apps/patient_manager/directives/templates/medication.html',
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
                if (form.name == '') return;
                form.search_str = scope.manual_medication.name;
                form.patient_id = scope.patient_id;
                medicationService.addMedication(form).then(function (data) {
                    scope.medications.push(data['medication']);
                    form.name = '';
                    scope.unset_new_medication();
                    toaster.pop('success', 'Done', 'Added medication!');
                    // Reset medication search terms after added to item
                    scope.manual_medication = {};
                    scope.medication_terms = [];
                });
            };

            scope.open_medication = function (medication) {
                $location.url('/medication/' + medication.id);
            };
        }
    }

}
