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
    angular.module('a1c', [])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .directive('a1c', a1cDirective);
    a1cDirective.$inject = ['CollapseService', 'a1cService', 'toaster', '$location', '$timeout', 'problemService', 'prompt', 'todoService', 'patientService', '$routeParams'];

    /**
     * @param CollapseService
     * @param a1cService
     * @param toaster
     * @param $location
     * @param $timeout
     * @param problemService
     * @param prompt
     * @param todoService
     * @param patientService
     * @param $routeParams
     * @returns {{restrict: string, templateUrl: string, scope: boolean, link: link}}
     */
    function a1cDirective(CollapseService, a1cService, toaster, $location, $timeout, problemService, prompt, todoService, patientService, $routeParams) {

        return {
            restrict: 'E',
            templateUrl: '/static/apps/patient/directives/a1c-directive/a1c.html',
            scope: {
                a1c: '=',
                orderAdded: '=',
                orderStatusChanged: '=',
                active_user: "=activeUser",
                labels: "=",
                members: "="
            },
            link: function (scope, element, attr, model) {


                scope.set_authentication_false = set_authentication_false;
                scope.open_a1c = open_a1c;
                scope.repeatThreeMonths = repeatThreeMonths;
                scope.add_note = add_note;
                scope.toggleEditNote = toggleEditNote;
                scope.toggleSaveNote = toggleSaveNote;
                scope.deleteNote = deleteNote;
                scope.a1cTodoStatusChangedCallback = a1cTodoStatusChangedCallback;

                init();

                scope.$on('todoListUpdated', (event, args) => {
                    scope.orders = patientService.getA1CToDo($routeParams.problem_id);
                });

                scope.$on('todoAdded', (event, args) => {
                    scope.orders = patientService.getA1CToDo($routeParams.problem_id);
                });

                function init() {
                    scope.orders = patientService.getA1CToDo($routeParams.problem_id);
                    // debugger;
                    scope.today = moment();

                    scope.show_a1c_collapse = CollapseService.show_a1c_collapse;

                    if (scope.a1c.a1c_todos)
                        if (scope.a1c.a1c_todos.length)
                            scope.a1c_date = moment(scope.a1c.a1c_todos[scope.a1c.a1c_todos.length - 1].due_date, "MM/DD/YYYY");

                    if (scope.a1c.observation.observation_components.length > 0)
                        scope.first_component = scope.a1c.observation.observation_components[0];

                    if (scope.first_component.observation_component_values.length > 0)
                        scope.last_value = scope.first_component.observation_component_values[scope.first_component.observation_component_values.length - 1];
                }

                function set_authentication_false() {
                    if (scope.problem) {
                        if (scope.active_user.role != "physician" && scope.active_user.role != "admin")
                            scope.problem.authenticated = false;
                    }
                }

                function open_a1c() {
                    if (!scope.show_a1c_collapse) {
                        var form = {};
                        form.a1c_id = scope.a1c.id;
                        a1cService.trackA1cClickEvent(form).then(function (data) {
                            CollapseService.ChangeA1cCollapse();
                            scope.show_a1c_collapse = CollapseService.show_a1c_collapse;
                        });
                    } else {
                        CollapseService.ChangeA1cCollapse();
                        scope.show_a1c_collapse = CollapseService.show_a1c_collapse;
                    }
                }

                function repeatThreeMonths() {
                    let form = {
                        name: "A1C",
                        patient_id: scope.patient_id,
                        problem_id: scope.a1c.problem.id,
                        a1c_id: scope.a1c.id,
                        due_date: moment().add(3, "months").format("MM/DD/YYYY"),
                    };

                    patientService.addProblemTodo(form).then((resp) => {
                        resp.success ? toaster.pop('success', 'Done', 'Added order!') : toaster.pop('error', 'Error', 'Repeat order failed!');

                        // Call parent page post order added
                        // scope.orderAdded(data.todo);

                        // scope.a1c.a1c_todos.push(data['todo']);
                        // scope.set_authentication_false();
                    });
                }

                function add_note(form) {
                    if (form.note == '') return;
                    form.a1c_id = scope.a1c.id;
                    a1cService.addNote(form).then(function (data) {
                        scope.a1c.a1c_notes.push(data['note']);
                        form.note = '';
                        toaster.pop('success', 'Done', 'Added Note!');
                    });
                }

                function toggleEditNote(note) {
                    note.edit = true;
                }

                function toggleSaveNote(note) {
                    a1cService.editNote(note).then(function (data) {
                        note.edit = false;
                        toaster.pop('success', 'Done', 'Edited note successfully');
                    });
                }

                function deleteNote(note) {
                    prompt({
                        "title": "Are you sure?",
                        "message": "Deleting a note is forever. There is no undo."
                    }).then(function (result) {
                        a1cService.deleteNote(note).then(function (data) {
                            var index = scope.a1c.a1c_notes.indexOf(note);
                            scope.a1c.a1c_notes.splice(index, 1);
                            toaster.pop('success', 'Done', 'Deleted note successfully');
                        });
                    }, function () {
                        return false;
                    });
                }

                function a1cTodoStatusChangedCallback(list, todo) {

                    // Remove it from itself todo list
                    let idx = list.indexOf(todo);
                    list.splice(idx, 1);

                    // Call parent page post order status changed
                    scope.orderStatusChanged(todo);
                }
            }
        }
    }
})();