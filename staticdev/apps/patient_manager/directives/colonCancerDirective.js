var colon_cancers = angular.module('colon_cancers', []);

colon_cancers.directive('colonCancer', ['toaster', '$location', '$timeout', 'prompt', 'CollapseService', 'colonService', colonCancerDirective]);

function colonCancerDirective(toaster, $location, $timeout, prompt, CollapseService, colonService) {

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

                            scope.delete_study = function(study) {
                                prompt({
                                    "title": "Are you sure?",
                                    "message": "Deleting a study is forever. There is no undo."
                                }).then(function(result){
                                    colonService.deleteStudy(study).then(function(data){
                                        var index = scope.colon_cancer.colon_studies.indexOf(study);
                                        scope.colon_cancer.colon_studies.splice(index, 1);
                                        toaster.pop('success', 'Done', 'Deleted study successfully');
                                    });
                                },function(){
                                    return false;
                                });
                            }
                        }
                    }, true);
                }
            }

};
