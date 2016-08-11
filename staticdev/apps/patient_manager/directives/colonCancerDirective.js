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

                            if (scope.colon_cancer.colon_studies) {
                                if (scope.colon_cancer.colon_studies.length > 0) {
                                    scope.todo_repeat = {};
                                    scope.todo_repeat.name = scope.colon_cancer.colon_studies[0].finding;
                                    scope.todo_repeat.year = moment().diff(scope.colon_cancer.colon_studies[0].study_date, 'years');
                                    if (scope.todo_repeat.year == 0) scope.todo_repeat.year = 1;
                                }
                            }

                            scope.set_header = function() {
                                scope.header = 'Colorectal cancer screening';
                                if (scope.colon_cancer.patient) {
                                    if (moment().diff(scope.colon_cancer.patient.date_of_birth, 'years') < 20) {
                                        scope.header = 'review risk assessment at 20 years of age';
                                    } else if (moment().diff(scope.colon_cancer.patient.date_of_birth, 'years') > 50) {
                                        if (scope.colon_cancer.risk) {
                                            scope.header = 'Risk: ' + scope.colon_cancer.risk;
                                        }
                                        if (scope.header != '') scope.header = scope.header + ' ';
                                        if (scope.colon_cancer.colon_cancer_todos.length > 0) {
                                            scope.most_recent_todo = scope.colon_cancer.colon_cancer_todos[scope.colon_cancer.colon_cancer_todos.length-1];
                                            scope.header = scope.header + 'Todo: ' + scope.most_recent_todo.todo + '. ';
                                            if (scope.most_recent_todo.due_date)
                                                scope.header = scope.header + moment(scope.most_recent_todo.due_date).format("MM/DD/YYYY")
                                        }
                                    } else {
                                        scope.header = 'screening starts at 50 years old';
                                    }
                                }
                            };
                            scope.set_header();

                            scope.open_colon = function(){
                                if (!scope.show_colon_collapse) {
                                    var form = {};
                                    form.colon_cancer_id = scope.colon_cancer.id;
                                    colonService.trackColonCancerClickEvent(form).then(function(data){
                                        CollapseService.ChangeColonCollapse();
                                        scope.show_colon_collapse = CollapseService.show_colon_collapse;
                                    });
                                }
                                else {
                                    CollapseService.ChangeColonCollapse();
                                    scope.show_colon_collapse = CollapseService.show_colon_collapse;
                                }
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
                                        scope.set_header();
                                    });
                                } else {
                                    colonService.deleteFactor(scope.colon_cancer.id, factor).then(function(data){
                                        toaster.pop('success', 'Done', 'Deleted factor successfully');
                                        scope.colon_cancer = data['info'];
                                        scope.set_header();
                                    });
                                }
                            };

                            scope.refuse = function() {
                                colonService.refuse(scope.colon_cancer.id).then(function(data){
                                    toaster.pop('success', 'Done', 'Refused successfully');
                                    scope.colon_cancer = data['info'];
                                });
                            };

                            scope.not_appropriate = function() {
                                colonService.not_appropriate(scope.colon_cancer.id).then(function(data){
                                    toaster.pop('success', 'Done', 'Set appropriate successfully');
                                    scope.colon_cancer = data['info'];
                                });
                            };

                            scope.repeat_todo = function(todo_repeat) {
                                form = {};
                                form.name = 'Repeat ' + todo_repeat.name + ' in ' + todo_repeat.year + ' years';
                                form.patient_id = scope.patient_id;
                                form.problem_id = scope.colon_cancer.problem.id;
                                form.colon_cancer_id = scope.colon_cancer.id;
                                problemService.addTodo(form).then(function(data){
                                    scope.problem_todos.push(data['todo']);
                                    scope.colon_cancer.colon_cancer_todos.push(data['todo']);
                                    toaster.pop('success', 'Done', 'Added Todo!');
                                });
                            };

                            // note
                            scope.add_note = function(form) {
                                if (form.note == '') return;
                                form.colon_cancer_id = scope.colon_cancer.id;
                                colonService.addNote(form).then(function(data) {
                                    scope.colon_cancer.colon_notes.push(data['note']);
                                    form.note = '';
                                    toaster.pop('success', 'Done', 'Added Note!');
                                });
                            }

                            scope.toggleEditNote = function(note) {
                                note.edit = true;
                            }

                            scope.toggleSaveNote = function(note) {
                                colonService.editNote(note).then(function(data) {
                                    note.edit = false;
                                    toaster.pop('success', 'Done', 'Edited note successfully');
                                });
                            }

                            scope.deleteNote = function(note) {
                                prompt({
                                    "title": "Are you sure?",
                                    "message": "Deleting a note is forever. There is no undo."
                                }).then(function(result){
                                    colonService.deleteNote(note).then(function(data){
                                        var index = scope.colon_cancer.colon_notes.indexOf(note);
                                        scope.colon_cancer.colon_notes.splice(index, 1);
                                        toaster.pop('success', 'Done', 'Deleted note successfully');
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
