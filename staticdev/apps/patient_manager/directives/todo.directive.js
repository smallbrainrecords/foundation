(function () {

    'use strict';


    angular.module('todos', ['sharedModule', 'ngDialog'])
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .directive('todo', todoDirective);

    todoDirective.$inject = ['todoService', 'patientService', 'toaster', '$location', '$timeout', 'sharedService', 'ngDialog', 'LABELS'];

    /**
     * Handle ordering todo list
     * @param todoService
     * @param patientService
     * @param toaster
     * @param $location
     * @param $timeout
     * @param sharedService
     * @param ngDialog
     * @param LABELS
     * @returns {{restrict: string, templateUrl: string, scope: {todoList: string, showProblem: string, patientId: string, userId: string, activeUser: string, labels: string, members: string, onStatusChangedSuccess: string}, link: link}}
     */
    function todoDirective(todoService, patientService, toaster, $location, $timeout, sharedService, ngDialog, LABELS) {

        return {
            restrict: 'E',
            templateUrl: '/static/apps/patient_manager/directives/templates/todo.html',
            scope: {
                todoList: '=',
                showProblem: '=',
                patientId: "=", // Migrate to data service
                userId: "=", // Migrate to data service
                activeUser: "=", // Migrate to data service
                labels: "=", // Migrate to data service
                members: "=", // Migrate to data service
            },
            link: link
        };

        function link(scope, element, attr, model) {
            var tmpList = scope.todoList;
            scope.sortingLog = [];
            scope.sorted = false;
            scope.dragged = false;
            scope.sortableOptions = {
                disabled: false,
                update: function (e, ui) {
                    scope.sorted = true;
                },
                start: function () {
                    scope.dragged = true;
                },
                stop: function (e, ui) {
                    // this callback has the changed model
                    if (scope.sorted) {
                        scope.sortingLog = [];
                        tmpList.map(function (i) {
                            scope.sortingLog.push(i.id);
                        });
                        let form = {
                            todos: scope.sortingLog,
                            patientId: scope.patientId
                        };

                        // TODO: Update the global data source also
                        patientService.updateTodoOrder(form)
                            .then((data) => {
                            toaster.pop('success', 'Done', 'Updated Todo Order');
                        });
                    }
                    scope.sorted = false;
                    $timeout(function () {
                        scope.dragged = false;
                    }, 100);
                }
            };

            scope.checkSharedProblem = checkSharedProblem;
            scope.onTodoEditStarted = onTodoEditStarted;
            scope.onTodoEditFinished = onTodoEditFinished;


            function checkSharedProblem(problem, sharing_patients) {
                if (scope.patientId === scope.userId || (scope.activeUser && scope.activeUser.role !== 'patient')) {
                    return true;
                } else {
                    let is_existed = false;
                    angular.forEach(sharing_patients, function (p, key) {
                        if (!is_existed && p.user.id === scope.userId) {
                            is_existed = scope.isInArray(p.problems, problem.id);
                        }
                    });

                    return is_existed;
                }
            }

            function onTodoEditStarted() {
                scope.sortableOptions.disabled = true;
            }

            function onTodoEditFinished() {
                scope.sortableOptions.disabled = false;
            }
        }
    }
})();