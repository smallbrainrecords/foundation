var colon_cancers = angular.module('colon_cancers', []);

colon_cancers.directive('colonCancer', ['toaster', '$location', '$timeout', 'prompt', 'CollapseService', colonCancerDirective]);

function colonCancerDirective(toaster, $location, $timeout, prompt, CollapseService) {

    var colonCancerObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/colon_cancer.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('observations', function(newVal, oldVal) {
                        if(newVal) {
                            scope.colon_cancer = scope.$eval(attr.ngModel);
                            scope.show_colon_collapse = CollapseService.show_colon_collapse;

                            scope.open_colon = function(){
                                CollapseService.ChangeColonCollapse();
                                scope.show_colon_collapse = CollapseService.show_colon_collapse;
                            };
                        }
                    }, true);
                }
            }

};
