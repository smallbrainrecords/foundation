var inr = angular.module('inr', []);

inr.directive('inr', ['CollapseService', 'toaster', '$location', '$timeout', 'prompt', 'inrService', inrDirective]);

function inrDirective(CollapseService, toaster, $location, $timeout, prompt, inrService) {

    var inrObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/inr.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('inrs', function(newVal, oldVal) {
                        if(newVal) {
                            scope.inr = scope.$eval(attr.ngModel);
                            scope.medication_terms = [];
                            scope.manual_medication = {};
                            scope.new_medication = {set: false};
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
                            
                        }
                    }, true);
                    scope.inrvalue = {};
                    if (scope.inrs.length>0){
                        inrService.getListProblem(scope.inrs[0].id).then(function(data){
                            scope.problems = data['data'];
                        });
                    }
                    scope.saveinrvalue = function(){
                        if (typeof(scope.inrvalue['value'])==='undefined' || scope.inrvalue['value']==null || typeof(scope.inrvalue['current_dose'])==='undefined' || scope.inrvalue['current_dose']==null || typeof(scope.inrvalue['effective_datetime'])==='undefined' || scope.inrvalue['effective_datetime']==null || typeof(scope.inrvalue['new_dosage'])==='undefined' || scope.inrvalue['new_dosage']==null || typeof(scope.inrvalue['next_inr'])==='undefined' || scope.inrvalue['next_inr']==null){
                            toaster.pop('warning', 'Warning', 'Please fill all field before save!');
                            return '';
                        }
                        scope.inrvalue['inr'] = scope.inrs[0].id;
                        scope.inrvalue['author_id'] = scope.inrs[0].author.id;
                        inrService.saveInrValue(scope.inrvalue).then(function(data){
                            if (data['success'] == true) {
                                toaster.pop('success', 'Done', 'Save inrvalue success!');
                                // scope.inrs[0].inr_values[scope.inrs[0].inr_values.length] = scope.inrvalue;
                                scope.inrs[0].inr_values.unshift(scope.inrvalue);
                                scope.inrvalue = {};
                            } else {
                                toaster.pop('error', 'Error', 'Can\'t save inrvalue!');
                            }
                        });
                    }
                    scope.checkradio = function(a){
                        scope.inr.target = parseInt(a.target);
                        inrService.setTargetforInr(a.id, a.target).then(function (data) {
                            if (data['success'] == true) {
                                toaster.pop('success', 'Done', 'Set target success!');
                            } else {
                                toaster.pop('error', 'Error', 'Can\'t set target , we are fixing it asap!');
                            }
                        });
                    }
                }
            }

};
