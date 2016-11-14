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
                    scope.popup2 = {};
                    scope.dateOptions = {
                        // dateDisabled: disabled,
                        formatYear: 'yy',
                        maxDate: new Date(2020, 5, 22),
                        minDate: new Date(),
                        startingDay: 1
                      };
                    // function disabled(data) {
                    //     var date = data.date,
                    //     mode = data.mode;
                    //     return mode === 'day' && (date.getDay() === 0 || date.getDay() === 6);
                    // }
                    // scope.inrvalue['effective_datetime'] = moment().format("YYYY-MM-DD HH:mm:ss");
                    scope.inrvalue.effective_datetime = moment().format("YYYY-MM-DD");
                    scope.inrvalue['next_inr'] = moment().add(1, 'month').format("YYYY-MM-DD HH:mm:ss");
                    if (scope.inrs.length>0){
                        inrService.getListProblem(scope.inrs[0].id).then(function(data){
                            scope.problems = data['data'];
                        });
                    }
                    scope.open2 = function() {
                        scope.popup2.opened = true;
                    };
                    scope.saveinrvalue = function(){
                        console.log(moment(scope.inrvalue['effective_datetime']).format("YYYY-MM-DD HH:mm:ss"))
                        if (typeof(scope.inrvalue['value'])==='undefined' || scope.inrvalue['value']==null || typeof(scope.inrvalue['current_dose'])==='undefined' || scope.inrvalue['current_dose']==null || typeof(scope.inrvalue['effective_datetime'])==='undefined' || scope.inrvalue['effective_datetime']==null || typeof(scope.inrvalue['new_dosage'])==='undefined' || scope.inrvalue['new_dosage']==null || typeof(scope.inrvalue['next_inr'])==='undefined' || scope.inrvalue['next_inr']==null){
                            toaster.pop('warning', 'Warning', 'Please fill all field before save!');
                            return '';
                        }
                        scope.inrvalue['inr'] = scope.inrs[0].id;
                        scope.inrvalue['author_id'] = scope.inrs[0].author.id;
                        inrService.saveInrValue(scope.inrvalue).then(function(data){
                            if (data['success'] == true) {
                                toaster.pop('success', 'Done', 'Save inrvalue success!');
                                scope.inrvalue['id'] = data['id'];
                                scope.inrvalue['ispatient'] = true;
                                scope.inrs[0].inr_values.unshift(scope.inrvalue);
                                scope.inrvalue = {};
                                scope.inrvalue['effective_datetime'] = moment().format("YYYY-MM-DD HH:mm:ss");
                            } else {
                                toaster.pop('error', 'Error', 'Can\'t save inrvalue!');
                            }
                        });
                    }
                    scope.initvalue = function(value){
                        value['isshow'] = false;
                        value['value'] = parseFloat(value['value']);
                        value['effective_datetime'] = moment(value['effective_datetime']).format("YYYY-MM-DD HH:mm:ss");
                        value['next_inr'] = moment(value['next_inr']).format("YYYY-MM-DD HH:mm:ss");
                    }
                    scope.editinrvalue = function(value, id){
                        if (value.isshow){
                            if (typeof(value['value'])==='undefined' || value['value']=="" || typeof(value['current_dose'])==='undefined' || value['current_dose']=="" || typeof(value['effective_datetime'])==='undefined' || value['effective_datetime']=="" || typeof(value['new_dosage'])==='undefined' || value['new_dosage']=="" || typeof(value['next_inr'])==='undefined' || value['next_inr']==""){
                                toaster.pop('warning', 'Warning', 'Please fill all field before save change!');
                                return '';
                            }
                            inrService.editInrValue(value, id).then(function(data){
                                if (data['success'] == true) {
                                    toaster.pop('success', 'Done', 'Edit inrvalue success!');
                                    value.isshow = !value.isshow;
                                } else {
                                    toaster.pop('error', 'Error', 'Can\'t edit Inrvalue!');
                                }
                            });
                        }else{
                            value.isshow = !value.isshow;
                        }
                    }
                    scope.deleteinrvalue = function(id, index, datas){
                        inrService.deleteInrValue(id).then(function(data){
                            if (data['success'] == true) {
                                toaster.pop('success', 'Done', 'Delete inrvalue success!');
                                datas.splice(index,1);
                            } else {
                                toaster.pop('error', 'Error', 'Can\'t delete Inrvalue!');
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
