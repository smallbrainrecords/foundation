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
        "use strict";

        angular.module('ManagerApp')
            .component('todoLaboratory', {
                templateUrl: "/static/apps/todo-laboratory/todo-laboratory.template.html",
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
            ctrl.activeUser = $rootScope.active_user;
            ctrl.todoId = parseInt($routeParams.todoId);
            ctrl.printForm = {};
            ctrl.todoLabels = [];
            ctrl.activeTodos = []; // Active Todos <-  Selected todo -> Todo & Problem
            ctrl.selectItemToPrint = selectItemToPrint;

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
                    problems: [] // text based array, labeled Associated diagnosis:

                };

                patientService.getToDo($rootScope.patient_id, false, true, 1).then((resp) => {
                    if (resp.success) {
                        ctrl.activeTodos = resp.data;

                        ctrl.activeTodos.map((todo, idx) => {
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
                                ctrl.todoLabels.push({
                                    id: item.id,
                                    name: item.name,
                                    css_class: item.css_class
                                });
                            }
                        }
                    }
                });


            };

            /**
             * Similar to ngAfterViewInit | ngAfterContentInit  in Angular
             */
            ctrl.$postLink = () => {

            };

            /**
             * Select todo item to print
             */
            function selectItemToPrint(event, todo, todoIdx) {
                if (ctrl.activeTodos[todoIdx].selected) {
                    // Remove selected todo & it associated diagnostics(if problem does not exist in any other selected todo)
                    let removingProblem = true; // Flag to determine whether or not problem should be removed. Default true
                    // Get position of selected todo inside selected item
                    ctrl.printForm.todos.map((item, index) => {
                        // Consideration of removing associated problem along with the todo if any other todo having
                        if (todo.problem != null && item.problem != null && todo.id !== item.id && todo.problem.id === item.problem.id) {
                            removingProblem = false;
                        }

                        // Remove the todo after removing problem
                        if (todo.id === item.id) {
                            ctrl.printForm.todos.splice(index, 1);
                            ctrl.activeTodos[todoIdx].selected = false;
                        }
                    });

                    if (removingProblem) {
                        ctrl.printForm.problems.map((item, index) => {
                            if (todo.problem.id === item.id) {
                                ctrl.printForm.problems.splice(index, 1);
                            }
                        });
                    }
                } else {
                    ctrl.printForm.todos.push(todo);
                    let addingProblem = true;
                    if (todo.problem != null) {
                        // Consideration of adding problem in to printed array
                        ctrl.printForm.problems.map((item) => {
                            if (todo.problem.id === item.id) {
                                addingProblem = false;
                            }
                        });

                        if (addingProblem) {
                            ctrl.printForm.problems.push(todo.problem);
                        }
                    }
                    ctrl.activeTodos[todoIdx].selected = true;
                }
            }

            event.stopPropagation();
        }
    }
)();