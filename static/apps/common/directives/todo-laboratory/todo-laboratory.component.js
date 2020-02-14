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
        "use strict";

        angular.module('ManagerApp')
            .component('todoLaboratory', {
                templateUrl: "/static/apps/common/directives/todo-laboratory/todo-laboratory.template.html",
                controller: todoLaboratoryController
            });

        /**
         *
         * @type {string[]}
         */
        todoLaboratoryController.$inject = ['$rootScope', '$scope', 'patientService', 'todoService', '$routeParams'];

        /**
         * TODO: Should I used $rootScope
         */
        function todoLaboratoryController($rootScope, $scope, patientService, todoService, $routeParams) {
            // Temporary solution for this (controllerAs syntax)
            let ctrl = this;

            ctrl.todoId = parseInt($routeParams.todoId);
            ctrl.activeUser = $rootScope.active_user;
            ctrl.patientProblems = [];
            ctrl.problem2Print=[];
            ctrl.patientTodos = [];
            ctrl.patientTodoLabels = [];
            ctrl.printForm = {};
            ctrl.itermediatedProblem2Print = {};

            ctrl.selectItemToPrint = selectItemToPrint;
            ctrl.saveDocument = saveDocument;
            ctrl.print = print;

            ctrl.$onInit = () => {
                ctrl.printForm = {
                    clinic: {
                        name: "Ryan Family Practice",
                        address: "300 S. Rath Ave, Suite 202",
                        address_2: "Ludington, MI 49431",
                        phone: "231 425 4447",
                        fax: "231 425 4401",
                        provider: "James Ryan D.O.",
                        NPINo: "1437271996"
                    },
                    patient: {
                        firstName: $rootScope.patient_info.user.first_name,
                        lastName: $rootScope.patient_info.user.last_name,
                        birthday: $rootScope.patient_info.date_of_birth,
                        sex: $rootScope.patient_info.sex,
                        phoneNumber: $rootScope.patient_info.phone_number
                    },
                    copied: "",
                    fax: "",
                    orderedAt: new Date(),
                    fasting: false,
                    notes: "", //labelled Special instructions:
                    todos: [], // text based array

                };

                patientService.getToDo($rootScope.patient_id, false, true, 1).then((resp) => {
                    if (resp.success) {
                        ctrl.patientTodos = resp.data;

                        ctrl.patientTodos.map((todo, idx) => {
                            if (todo.id == ctrl.todoId) {
                                selectItemToPrint(null, todo, idx);
                            }
                        });

                        // Load all label for all user
                        let allLabels = _.flatten(_.pluck(resp.data, 'labels'));
                        const map = new Map();
                        for (const item of allLabels) {
                            if (!map.has(item.id)) {
                                map.set(item.id, true);    // set any value to Map
                                ctrl.patientTodoLabels.push({
                                    id: item.id,
                                    name: item.name,
                                    css_class: item.css_class
                                });
                            }
                        }
                    }
                });

                patientService.getProblems($rootScope.patient_id).then((resp) => {
                    if (resp.data.success)
                        ctrl.patientProblems = resp.data.data;
                });
            };

            /**
             * Select todo item to print
             */
            function selectItemToPrint(event, todo, todoIdx) {
                if (ctrl.patientTodos[todoIdx].selected) {
                    ctrl.printForm.todos.map((item, index) => {
                        if (todo.id === item.id) {
                            ctrl.printForm.todos.splice(index, 1);
                            ctrl.patientTodos[todoIdx].selected = false;
                        }
                    });

                    delete ctrl.itermediatedProblem2Print[todo.id];
                } else {
                    ctrl.printForm.todos.push(todo);
                    ctrl.patientTodos[todoIdx].selected = true;

                    if (todo.problem) {
                        ctrl.itermediatedProblem2Print[todo.id] = todo.problem;
                    }
                }

                // 1. Get all selected values
                let problems = Object.values(ctrl.itermediatedProblem2Print);

                // 2. Get all problems id
                let problemIds = _.pluck(problems, 'id');
                let effectedIds = _.pluck(problems, 'effected').flat();
                let effectingIds = _.pluck(problems, 'effecting').flat();

                // 3. Distinct items
                ctrl.problem2Print = [...new Set(problemIds.concat(effectedIds, effectingIds))];
            }

            function saveDocument() {
                // Generate PDF
                let opt = {
                    margin: 10
                };
                let printEle = document.getElementById("print-template");
                html2pdf().set(opt).from(printEle.innerHTML).save(`Todo Laboratory for ${$rootScope.patient_info.user.first_name} ${$rootScope.patient_info.user.last_name}_${Date.now()}`);
            }

            function print() {
                // TODO: How to save activities log only when user is successfully print the todo laboratory.
                // An exception case is user show print preview but doesn't print actually.
                todoService.saveTodoPrintLogs(ctrl.printForm.todos);
            }
        }
    }
)();