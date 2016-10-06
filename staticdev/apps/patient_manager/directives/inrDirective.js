var inr = angular.module('inr', []);

inr.directive('inr', ['CollapseService', 'toaster', '$location', '$timeout', 'prompt', 'inrService', inrDirective]);

function inrDirective(CollapseService, toaster, $location, $timeout, prompt, inrService) {

    var inrObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/inr.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('inr.patient', function(newVal, oldVal) {
                        if(newVal) {
                            scope.inr = scope.$eval(attr.ngModel);
                            
                            scope.open_inr = function(){
                                if (!scope.show_inr_collapse) {
                                    CollapseService.ChangeInrCollapse();
                                    scope.show_inr_collapse = CollapseService.show_inr_collapse;
                                }
                                else {
                                    CollapseService.ChangeInrCollapse();
                                    scope.show_inr_collapse = CollapseService.show_inr_collapse;
                                }
                            };

                            scope.add_medication = function(form) {
                                if (form.name == '') return;
                                form.inr_id = scope.inr.id;
                                form.patient_id = scope.patient_id;
                                inrService.addMedication(form).then(function(data) {
                                    scope.inr.inr_medications.push(data['medication']);
                                    form.name = '';
                                    toaster.pop('success', 'Done', 'Added medication!');
                                });
                            };

                            scope.open_medication = function(medication) {
                                $location.url('/inr/medication/' + medication.id);
                            };
                        }
                    }, true);
                }
            }

};
