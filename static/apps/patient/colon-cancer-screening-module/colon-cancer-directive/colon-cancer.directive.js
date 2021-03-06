/*
 * Copyright (c) Small Brain Records 2014-2020. Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
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
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */
(function () {

    'use strict';

    angular.module('colon_cancers')
        .directive('colonCancer', colonCancerDirective);
    colonCancerDirective.$inject = ['toaster', 'prompt', 'CollapseService', 'colonService', 'problemService', 'patientService', '$routeParams'];

    function colonCancerDirective(toaster, prompt, CollapseService, colonService, problemService, patientService, $routeParams) {
        return {
            restrict: 'E',
            templateUrl: '/static/apps/patient/colon-cancer-screening-module/colon-cancer-directive/colon-cancer.html',
            scope: {
                colon_cancer: '=colonCancer',
                orderAdded: '=',
                orderStatusChanged: '=',
                active_user: "=activeUser",
                labels: "=",
                members: "="
            },
            link: function (scope, element, attr) {
                scope.showFactors = false;
                scope.set_header = generateHeaderTitle;
                scope.show_note = false
                scope.see_past_studies = false;
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

                scope.openColon = openColon;
                scope.deleteStudy = deleteStudy;
                scope.changeFactor = changeFactor;
                scope.refuse = refuse;
                scope.notAppropriate = notAppropriate;
                scope.repeatTodo = repeatTodo;
                scope.addNote = addNote;
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


                    angular.forEach(scope.colon_cancer.colon_risk_factors, function (colon_risk_factor, key) {
                        angular.forEach(scope.factors, function (factor, key) {
                            if (colon_risk_factor.factor === factor.value) {
                                factor.checked = true;
                            }
                        });
                    });

                    if (scope.colon_cancer.colon_studies) {
                        if (scope.colon_cancer.colon_studies.length > 0) {
                            scope.todo_repeat = {};
                            scope.last_study = scope.colon_cancer.colon_studies[0];
                            scope.todo_repeat.name = scope.last_study.finding;

                            if (scope.last_study.finding === 'fecal occult blood test' || scope.last_study.finding === 'fecal immunochemical test') {
                                scope.todo_repeat.year = 1;
                            } else if (scope.last_study.finding === 'colonoscopy') {
                                if (scope.last_study.result === 'no polyps') {
                                    scope.todo_repeat.year = 10;
                                } else if (scope.last_study.result === 'adenomatous polyps' || scope.last_study.result === 'serrated polyps') {
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


                function generateHeaderTitle() {
                    scope.header = '';
                    if (scope.colon_cancer.patient) {
                        if (moment().diff(moment(scope.colon_cancer.patient.profile.date_of_birth, "MM/DD/YYYY"), 'years') < 20) {
                            scope.header = 'Review risk assessment at 20 years of age';
                        } else if (moment().diff(moment(scope.colon_cancer.patient.profile.date_of_birth, "MM/DD/YYYY"), 'years') > 50) {
                            // Adding risk status to header
                            if (scope.colon_cancer.risk) {
                                scope.header = `Risk:${scope.colon_cancer.risk},`;
                            }

                            if (scope.colon_cancer.colon_studies.length > 0) {
                                scope.header = `${scope.header} Last finding: ${scope.colon_cancer.colon_studies[0].finding} `;
                            }
                            // if (scope.header != '') scope.header = scope.header + ' ';

                            // TODO: Doest both refused and not appropriate are active?
                            let texts = [];
                            if (scope.colon_cancer.patient_refused) {
                                texts.push({
                                    text: "Refused on " + moment(scope.colon_cancer.patient_refused_on).format("MM/DD/YYYY"),
                                    date: moment(scope.colon_cancer.patient_refused_on)
                                });
                            }

                            if (scope.colon_cancer.notAppropriate) {
                                texts.push({
                                    text: "Not appropriate on " + moment(scope.colon_cancer.not_appropriate_on).format("MM/DD/YYYY"),
                                    date: moment(scope.colon_cancer.not_appropriate_on)
                                });
                            }

                            if (scope.colon_cancer.colon_cancer_todos.length > 0) {
                                scope.most_recent_todo = scope.colon_cancer.colon_cancer_todos[scope.colon_cancer.colon_cancer_todos.length - 1];
                                let text = {};
                                text['text'] = `Todo: ${scope.most_recent_todo.todo}`;
                                if (scope.most_recent_todo.due_date)
                                    text['text'] = `${text['text']} ${moment(scope.most_recent_todo.due_date, "MM/DD/YYYY").format("MM/DD/YYYY")}`;
                                text['date'] = moment(scope.most_recent_todo.created_on);
                                texts.push(text);
                            }

                            let picked = {};
                            for (let i = 0; i < texts.length; i++) {
                                if (picked.date === undefined) {
                                    picked = texts[i];
                                } else if (picked.date < texts[i].date) {
                                    picked = texts[i];
                                }
                            }

                            if (!$.isEmptyObject(picked)) {
                                scope.header = scope.header + picked['text'];
                            }

                        } else {
                            scope.header = 'Screening starts at 50 years old';
                        }
                    }
                }

                function openColon() {
                    if (!scope.show_colon_collapse) {
                        var form = {};
                        form.colon_cancer_id = scope.colon_cancer.id;
                        colonService.trackColonCancerClickEvent(form).then(function (response) {
                            let data = response.data;
                            CollapseService.ChangeColonCollapse();
                            scope.show_colon_collapse = CollapseService.show_colon_collapse;
                        });
                    } else {
                        CollapseService.ChangeColonCollapse();
                        scope.show_colon_collapse = CollapseService.show_colon_collapse;
                    }
                }

                function deleteStudy(study) {
                    prompt({
                        "title": "Are you sure?",
                        "message": "Deleting a study is forever. There is no undo."
                    }).then(function (result) {
                        colonService.deleteStudy(study).then(function (response) {
                            let data = response.data;
                            var index = scope.colon_cancer.colon_studies.indexOf(study);
                            scope.colon_cancer.colon_studies.splice(index, 1);
                            toaster.pop('success', 'Done', 'Deleted study successfully');
                        });
                    }, function () {
                        return false;
                    });
                }

                function changeFactor(factor) {
                    if (factor.checked) {
                        colonService.addFactor(scope.colon_cancer.id, factor).then(function (response) {
                            let data = response.data;
                            toaster.pop('success', 'Done', 'Added factor successfully');
                            scope.colon_cancer = data['info'];
                            angular.forEach(scope.factors, function (factor, key) {
                                factor.checked = false;
                            });
                            angular.forEach(scope.colon_cancer.colon_risk_factors, function (colon_risk_factor, key) {
                                angular.forEach(scope.factors, function (factor, key) {
                                    if (colon_risk_factor.factor === factor.value) {
                                        factor.checked = true;
                                    }
                                });
                            });
                            scope.set_header();
                        });
                    } else {
                        colonService.deleteFactor(scope.colon_cancer.id, factor).then(function (response) {
                            let data = response.data;
                            toaster.pop('success', 'Done', 'Deleted factor successfully');
                            scope.colon_cancer = data['info'];
                            scope.set_header();
                        });
                    }
                }

                function refuse() {
                    colonService.refuse(scope.colon_cancer.id).then(function (response) {
                        let data = response.data;
                        toaster.pop('success', 'Done', 'Refused successfully');
                        scope.colon_cancer = data['info'];
                        scope.set_header();
                    });
                }

                function notAppropriate() {
                    colonService.notAppropriate(scope.colon_cancer.id).then(function (response) {
                        let data = response.data;
                        toaster.pop('success', 'Done', 'Set appropriate successfully');
                        scope.colon_cancer = data['info'];
                        scope.set_header();
                    });
                }

                function repeatTodo(todo_repeat) {
                    let form = {
                        name: todo_repeat.name,
                        due_date: todo_repeat.due_date,
                        patient_id: scope.patient_id,
                        problem_id: scope.colon_cancer.problem.id,
                        colon_cancer_id: scope.colon_cancer.id,
                    };

                    patientService.addProblemTodo(form).then((response) => {
                        let data = response.data;
                        toaster.pop('success', 'Done', 'Added Todo!');
                        scope.set_header();
                    });

                }

                // note
                function addNote(form) {
                    if (_.isEmpty(form.note))
                        return;

                    form.colon_cancer_id = scope.colon_cancer.id;

                    colonService.addNote(form).then(function (response) {
                        let data = response.data;
                        scope.colon_cancer.colon_notes.push(data['note']);
                        form.note = '';
                        toaster.pop('success', 'Done', 'Added Note!');
                    });
                }

                function toggleEditNote(note) {
                    note.edit = true;
                }

                function toggleSaveNote(note) {
                    colonService.editNote(note).then(function (response) {
                        let data = response.data;
                        note.edit = false;
                        toaster.pop('success', 'Done', 'Edited note successfully');
                    });
                }

                function deleteNote(note) {
                    prompt({
                        "title": "Are you sure?",
                        "message": "Deleting a note is forever. There is no undo."
                    }).then(function (result) {
                        colonService.deleteNote(note).then(function (response) {
                            let data = response.data;
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
                    }
                }
            }
        }

    }
})();