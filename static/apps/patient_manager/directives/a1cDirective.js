(function () {

    'use strict';
    angular.module('a1c', [])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .directive('a1c', a1cDirective);
    a1cDirective.$inject = ['CollapseService', 'a1cService', 'toaster', '$location', '$timeout', 'problemService', 'prompt', 'todoService'];

    /**
     * @param CollapseService
     * @param a1cService
     * @param toaster
     * @param $location
     * @param $timeout
     * @param problemService
     * @param prompt
     * @param todoService
     * @returns {{restrict: string, templateUrl: string, scope: boolean, link: link}}
     */
    function a1cDirective(CollapseService, a1cService, toaster, $location, $timeout, problemService, prompt, todoService) {

        return {
            restrict: 'E',
            templateUrl: '/static/apps/patient_manager/directives/templates/a1c.html',
            scope: {
                a1c: '=',
                orderAdded: '=',
                orderStatusChanged: '=',
                active_user: "=activeUser",
                labels: "=",
                members: "="
            },
            link: function (scope, element, attr, model) {
                scope.today = moment();
                scope.show_a1c_collapse = CollapseService.show_a1c_collapse;
                if (scope.a1c.a1c_todos)
                    if (scope.a1c.a1c_todos.length)
                        scope.a1c_date = moment(scope.a1c.a1c_todos[scope.a1c.a1c_todos.length - 1].due_date, "MM/DD/YYYY");

                if (scope.a1c.observation.observation_components.length > 0)
                    scope.first_component = scope.a1c.observation.observation_components[0];
                if (scope.first_component.observation_component_values.length > 0)
                    scope.last_value = scope.first_component.observation_component_values[scope.first_component.observation_component_values.length - 1];

                scope.set_authentication_false = function () {
                    if (scope.problem) {
                        if (scope.active_user.role != "physician" && scope.active_user.role != "admin")
                            scope.problem.authenticated = false;
                    }
                };

                scope.open_a1c = function () {
                    if (!scope.show_a1c_collapse) {
                        var form = {};
                        form.a1c_id = scope.a1c.id;
                        a1cService.trackA1cClickEvent(form).then(function (data) {
                            CollapseService.ChangeA1cCollapse();
                            scope.show_a1c_collapse = CollapseService.show_a1c_collapse;
                        });
                    }
                    else {
                        CollapseService.ChangeA1cCollapse();
                        scope.show_a1c_collapse = CollapseService.show_a1c_collapse;
                    }
                };

                scope.repeatThreeMonths = function () {
                    let form = {};
                    form.name = "A1C";
                    form.patient_id = scope.patient_id;
                    form.problem_id = scope.a1c.problem.id;
                    form.a1c_id = scope.a1c.id;
                    form.due_date = moment().add(3, "months").format("MM/DD/YYYY");
                    problemService.addTodo(form).then(function (data) {
                        toaster.pop('success', 'Done', 'Added Todo!');

                        // Call parent page post order added
                        scope.orderAdded(data.todo);

                        scope.a1c.a1c_todos.push(data['todo']);
                        scope.set_authentication_false();
                    });
                };

                scope.add_note = function (form) {
                    if (form.note == '') return;
                    form.a1c_id = scope.a1c.id;
                    a1cService.addNote(form).then(function (data) {
                        scope.a1c.a1c_notes.push(data['note']);
                        form.note = '';
                        toaster.pop('success', 'Done', 'Added Note!');
                    });
                };

                scope.toggleEditNote = function (note) {
                    note.edit = true;
                };

                scope.toggleSaveNote = function (note) {
                    a1cService.editNote(note).then(function (data) {
                        note.edit = false;
                        toaster.pop('success', 'Done', 'Edited note successfully');
                    });
                };

                scope.deleteNote = function (note) {
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
                };

                scope.a1cTodoStatusChangedCallback = function (list, todo) {

                    // Remove it from itself todo list
                    let idx = list.indexOf(todo);
                    list.splice(idx, 1);

                    // Call parent page post order status changed
                    scope.orderStatusChanged(todo);
                };
            }
        }
    }
})();