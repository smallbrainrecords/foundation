/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
(function () {

    'use strict';

    angular.module('colon_cancers', []).config(function ($httpProvider) {
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    }).directive('colonCancer', colonCancerDirective);
    colonCancerDirective.$inject = ['toaster', 'prompt', 'CollapseService', 'colonService', 'problemService', 'patientService', '$routeParams'];

    function colonCancerDirective(toaster, prompt, CollapseService, colonService, problemService, patientService, $routeParams) {
        return {
            restrict: 'E',
            templateUrl: '/static/apps/patient_manager/directives/templates/colon_cancer.html',
            scope: {
                colon_cancer: '=colonCancer',
                orderAdded: '=',
                orderStatusChanged: '=',
                active_user: "=activeUser",
                labels: "=",
                members: "="
            },
            link: function (scope, element, attr) {
                scope.set_header = set_header;
                scope.open_colon = open_colon;
                scope.delete_study = delete_study;
                scope.change_factor = change_factor;
                scope.refuse = refuse;
                scope.not_appropriate = not_appropriate;
                scope.repeat_todo = repeat_todo;
                scope.add_note = add_note;
                scope.toggleEditNote = toggleEditNote;
                scope.toggleSaveNote = toggleSaveNote;
                scope.deleteNote = deleteNote;
                scope.todoStatusChanged = todoStatusChanged;
                scope.addNewOrder = addNewOrder;
                init();

                scope.$on('todoListUpdated', (event, args) => {
                    scope.orders = patientService.getColonCancerToDo($routeParams.problem_id);
                });

                scope.$on('todoAdded', (event, args) => {
                    scope.orders = patientService.getColonCancerToDo($routeParams.problem_id);
                });

                function init() {
                    scope.orders = patientService.getColonCancerToDo($routeParams.problem_id);

                    scope.show_colon_collapse = CollapseService.show_colon_collapse;

                    scope.factors = [
                        {value: 'no known risk', checked: false},
                        {value: 'personal history of colorectal cancer', checked: false},
                        {value: 'personal history of adenomatous polyp', checked: false},
                        {value: "personal history of ulcerative colitis or Crohn's disease", checked: false},
                        {value: 'abdominal radiation for childhood cancer', checked: false},
                        {value: 'family history of colorectal cancer or an adenomatous polyp', checked: false},
                        {
                            value: 'High-risk genetic syndromes: Lynch syndrome or Familial adenomatous polyposis',
                            checked: false
                        },
                    ];

                    angular.forEach(scope.colon_cancer.colon_risk_factors, function (colon_risk_factor, key) {
                        angular.forEach(scope.factors, function (factor, key) {
                            if (colon_risk_factor.factor == factor.value) {
                                factor.checked = true;
                            }
                        });
                    });

                    if (scope.colon_cancer.colon_studies) {
                        if (scope.colon_cancer.colon_studies.length > 0) {
                            scope.todo_repeat = {};
                            scope.last_study = scope.colon_cancer.colon_studies[0];
                            scope.todo_repeat.name = scope.last_study.finding;

                            if (scope.last_study.finding == 'fecal occult blood test' || scope.last_study.finding == 'fecal immunochemical test') {
                                scope.todo_repeat.year = 1;
                            } else if (scope.last_study.finding == 'colonoscopy') {
                                if (scope.last_study.result == 'no polyps') {
                                    scope.todo_repeat.year = 10;
                                } else if (scope.last_study.result == 'adenomatous polyps' || scope.last_study.result == 'serrated polyps') {
                                    scope.todo_repeat.year = 3;
                                    scope.todo_repeat.name = 'surveillance colonoscopy for high risk polyp';
                                } else {
                                    scope.todo_repeat.year = 0;
                                }
                            } else {
                                scope.todo_repeat.year = 0;
                            }

                            scope.todo_repeat.due_date = moment(scope.last_study.study_date).add(scope.todo_repeat.year, "years").format("MM/DD/YYYY");
                        }
                    }

                    scope.set_header();

                }

                function set_header() {
                    scope.header = '';
                    if (scope.colon_cancer.patient) {
                        if (moment().diff(moment(scope.colon_cancer.patient.profile.date_of_birth, "MM/DD/YYYY"), 'years') < 20) {
                            scope.header = 'review risk assessment at 20 years of age';
                        } else if (moment().diff(moment(scope.colon_cancer.patient.profile.date_of_birth, "MM/DD/YYYY"), 'years') > 50) {
                            if (scope.colon_cancer.risk) {
                                scope.header = 'Risk: ' + scope.colon_cancer.risk;
                            }
                            if (scope.header != '') scope.header = scope.header + ' ';

                            var texts = [];
                            if (scope.colon_cancer.patient_refused) {
                                texts.push({
                                    text: "Refused on " + moment(scope.colon_cancer.patient_refused_on).format("MM/DD/YYYY"),
                                    date: moment(scope.colon_cancer.patient_refused_on)
                                });
                            }
                            if (scope.colon_cancer.not_appropriate) {
                                texts.push({
                                    text: "Not appropriate on " + moment(scope.colon_cancer.not_appropriate_on).format("MM/DD/YYYY"),
                                    date: moment(scope.colon_cancer.not_appropriate_on)
                                });
                            }
                            if (scope.colon_cancer.colon_cancer_todos.length > 0) {
                                scope.most_recent_todo = scope.colon_cancer.colon_cancer_todos[scope.colon_cancer.colon_cancer_todos.length - 1];
                                var text = {};
                                text['text'] = 'Todo: ' + scope.most_recent_todo.todo;
                                if (scope.most_recent_todo.due_date)
                                    text['text'] = text['text'] + ' ' + moment(scope.most_recent_todo.due_date, "MM/DD/YYYY").format("MM/DD/YYYY");
                                text['date'] = moment(scope.most_recent_todo.created_on);
                                texts.push(text);
                            }
                            var picked = {};
                            for (var i = 0; i < texts.length; i++) {
                                if (picked.date == undefined) {
                                    picked = texts[i];
                                } else if (picked.date < texts[i].date) {
                                    picked = texts[i];
                                }
                            }
                            if (!$.isEmptyObject(picked)) {
                                scope.header = scope.header + picked['text'];
                            }

                        } else {
                            scope.header = 'screening starts at 50 years old';
                        }
                    }
                }

                function open_colon() {
                    if (!scope.show_colon_collapse) {
                        var form = {};
                        form.colon_cancer_id = scope.colon_cancer.id;
                        colonService.trackColonCancerClickEvent(form).then(function (data) {
                            CollapseService.ChangeColonCollapse();
                            scope.show_colon_collapse = CollapseService.show_colon_collapse;
                        });
                    }
                    else {
                        CollapseService.ChangeColonCollapse();
                        scope.show_colon_collapse = CollapseService.show_colon_collapse;
                    }
                }

                function delete_study(study) {
                    prompt({
                        "title": "Are you sure?",
                        "message": "Deleting a study is forever. There is no undo."
                    }).then(function (result) {
                        colonService.deleteStudy(study).then(function (data) {
                            var index = scope.colon_cancer.colon_studies.indexOf(study);
                            scope.colon_cancer.colon_studies.splice(index, 1);
                            toaster.pop('success', 'Done', 'Deleted study successfully');
                        });
                    }, function () {
                        return false;
                    });
                }

                function change_factor(factor) {
                    if (factor.checked) {
                        colonService.addFactor(scope.colon_cancer.id, factor).then(function (data) {
                            toaster.pop('success', 'Done', 'Added factor successfully');
                            scope.colon_cancer = data['info'];
                            angular.forEach(scope.factors, function (factor, key) {
                                factor.checked = false;
                            });
                            angular.forEach(scope.colon_cancer.colon_risk_factors, function (colon_risk_factor, key) {
                                angular.forEach(scope.factors, function (factor, key) {
                                    if (colon_risk_factor.factor == factor.value) {
                                        factor.checked = true;
                                    }
                                });
                            });
                            scope.set_header();
                        });
                    } else {
                        colonService.deleteFactor(scope.colon_cancer.id, factor).then(function (data) {
                            toaster.pop('success', 'Done', 'Deleted factor successfully');
                            scope.colon_cancer = data['info'];
                            scope.set_header();
                        });
                    }
                }

                function refuse() {
                    colonService.refuse(scope.colon_cancer.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Refused successfully');
                        scope.colon_cancer = data['info'];
                        scope.set_header();
                    });
                }

                function not_appropriate() {
                    colonService.not_appropriate(scope.colon_cancer.id).then(function (data) {
                        toaster.pop('success', 'Done', 'Set appropriate successfully');
                        scope.colon_cancer = data['info'];
                        scope.set_header();
                    });
                }

                function repeat_todo(todo_repeat) {
                    let form = {
                        name: todo_repeat.name,
                        due_date: todo_repeat.due_date,
                        patient_id: scope.patient_id,
                        problem_id: scope.colon_cancer.problem.id,
                        colon_cancer_id: scope.colon_cancer.id,
                    };

                    patientService.addProblemTodo(form).then((data) => {
                        // scope.problem_todos.push(data['todo']);
                        // scope.orderAdded(data.todo);

                        // scope.colon_cancer.colon_cancer_todos.push(data['todo']);
                        toaster.pop('success', 'Done', 'Added Todo!');
                        scope.set_header();
                    });

                    // problemService.addTodo(form).then((data) => {
                    //     // scope.problem_todos.push(data['todo']);
                    //     scope.orderAdded(data.todo);
                    //
                    //     scope.colon_cancer.colon_cancer_todos.push(data['todo']);
                    //     toaster.pop('success', 'Done', 'Added Todo!');
                    //     scope.set_header();
                    // });
                }
                // note
                function add_note(form) {
                    if (_.isEmpty(form.note))
                        return;

                    form.colon_cancer_id = scope.colon_cancer.id;

                    colonService.addNote(form).then(function (data) {
                        scope.colon_cancer.colon_notes.push(data['note']);
                        form.note = '';
                        toaster.pop('success', 'Done', 'Added Note!');
                    });
                }

                function toggleEditNote(note) {
                    note.edit = true;
                }

                function toggleSaveNote(note) {
                    colonService.editNote(note).then(function (data) {
                        note.edit = false;
                        toaster.pop('success', 'Done', 'Edited note successfully');
                    });
                }

                function deleteNote(note) {
                    prompt({
                        "title": "Are you sure?",
                        "message": "Deleting a note is forever. There is no undo."
                    }).then(function (result) {
                        colonService.deleteNote(note).then(function (data) {
                            var index = scope.colon_cancer.colon_notes.indexOf(note);
                            scope.colon_cancer.colon_notes.splice(index, 1);
                            toaster.pop('success', 'Done', 'Deleted note successfully');
                        });
                    }, function () {
                        return false;
                    });
                }

                /**
                 * @deprecated
                 * @param list
                 * @param todo
                 */
                function todoStatusChanged(list, todo) {
                    debugger;
                    // Remove it from itself todo list
                    let idx = list.indexOf(todo);
                    list.splice(idx, 1);

                    // Call parent page post order status changed
                    scope.orderStatusChanged(todo);
                }

                function addNewOrder(form) {
                    if (_.isUndefined(form) && _.isEmpty(form.name)) {
                        return false;
                    }

                    form.patient_id = scope.patient_id;
                    form.problem_id = scope.colon_cancer.problem.id;
                    form.colon_cancer_id = scope.colon_cancer.id;

                    // TODO: Performances report
                    if (scope.bleeding_risk) {
                        let bleedingRiskDialog = ngDialog.open({
                            template: 'bleedingRiskDialog',
                            showClose: false,
                            closeByEscape: false,
                            closeByDocument: false,
                            closeByNavigation: false
                        });

                        bleedingRiskDialog.closePromise.then(function () {
                            patientService.addProblemTodo(form).then(addTodoSuccess);
                        });
                    } else {
                        patientService.addProblemTodo(form).then(addTodoSuccess);
                    }

                    // Add todo succeeded
                    function addTodoSuccess(data) {
                        form.name = '';
                        toaster.pop('success', 'Done', 'Added Todo!');
                        // $location.url('/problem/' + $scope.colon_cancer.problem.id);
                    }
                }
            }
        }

    }
})();