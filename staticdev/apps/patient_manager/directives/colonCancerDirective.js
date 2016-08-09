var colon_cancers = angular.module('colon_cancers', []);

colon_cancers.directive('colonCancer', ['toaster', '$location', '$timeout', 'prompt', 'CollapseService', 'colonService', 'problemService', colonCancerDirective]);

function colonCancerDirective(toaster, $location, $timeout, prompt, CollapseService, colonService, problemService) {

    var colonCancerObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/colon_cancer.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('colon_cancers', function(newVal, oldVal) {
                        if(newVal) {
                            scope.colon_cancer = scope.$eval(attr.ngModel);
                            scope.show_colon_collapse = CollapseService.show_colon_collapse;

                            scope.factors = [
                                {value: 'no known risk', checked: false},
                                {value: 'personal history of colorectal cancer', checked: false},
                                {value: 'personal history of adenomatous polyp', checked: false},
                                {value: "personal history of ulcerative colitis or Crohn's disease", checked: false},
                                {value: 'abdominal radiation for childhood cancer', checked: false},
                                {value: 'family history of colorectal cancer or an adenomatous polyp', checked: false},
                                {value: 'High-risk genetic syndromes: Lynch syndrome or Familial adenomatous polyposis', checked: false},
                            ];

                            angular.forEach(scope.colon_cancer.colon_risk_factors, function(colon_risk_factor, key) {
                                angular.forEach(scope.factors, function(factor, key) {
                                    if (colon_risk_factor.factor == factor.value) {
                                        factor.checked = true;
                                    }
                                });
                            });

                            if (scope.colon_cancer.patient) {
                                if(!scope.colon_cancer.todo_past_five_years && moment().diff(scope.colon_cancer.patient.date_of_birth, 'years') >= 20 && (scope.colon_cancer.colon_risk_factors.length==0 || moment().diff(scope.colon_cancer.last_risk_updated_date, 'years') >= 5)) {
                                    form = {};
                                    form.name = 'review colorectal cancer risk assessment';
                                    form.patient_id = scope.patient_id;
                                    form.problem_id = scope.colon_cancer.problem.id;
                                    form.colon_cancer_id = scope.colon_cancer.id;
                                    form.todo_past_five_years = true;
                                    problemService.addTodo(form).then(function(data){
                                        scope.problem_todos.push(data['todo']);
                                        toaster.pop('success', 'Done', 'Added Todo!');
                                    });
                                }
                            }

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
                            };

                            scope.change_factor = function(factor) {
                                if (factor.checked){
                                    colonService.addFactor(scope.colon_cancer.id, factor).then(function(data){
                                        toaster.pop('success', 'Done', 'Added factor successfully');
                                        scope.colon_cancer = data['info'];
                                    });
                                } else {
                                    colonService.deleteFactor(scope.colon_cancer.id, factor).then(function(data){
                                        toaster.pop('success', 'Done', 'Deleted factor successfully');
                                        scope.colon_cancer = data['info'];
                                    });
                                }
                            }
                        }
                    }, true);
                }
            }

};
