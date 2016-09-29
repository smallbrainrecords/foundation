var medication = angular.module('medication', []);

medication.directive('medication', ['CollapseService', 'toaster', '$location', '$timeout', 'prompt', medicationDirective]);

function medicationDirective(CollapseService, toaster, $location, $timeout, prompt) {

    var medicationObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/medication.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('medication', function(newVal, oldVal) {
                        if(newVal) {
                            scope.medication = scope.$eval(attr.ngModel);
                            
                        }
                    }, true);
                }
            }

};
