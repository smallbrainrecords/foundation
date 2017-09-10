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
                // onStatusChangedSuccess: "=onStatusChangedSuccess" // deprecated
            },
            link: link
        };

        function link(scope, element, attr, model) {
            scope.allowDueDateNotification = true;
            var currentTodo;
            // TODO: Investigate the usage of this variable
            scope.current_todo = null;

            var tmpList = scope.todoList;
            scope.sortingLog = [];
            scope.sorted = false;
            scope.dragged = false;
            scope.labels_component = LABELS;
            scope.label_component = {};
            scope.todos_ready = false;
            scope.sortableOptions = {
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

                        patientService.updateTodoOrder(form).then(function (data) {
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
            scope.isDueDate = isDueDate;
            scope.updateTodoStatus = updateTodoStatus;
            scope.open_todo = open_todo;
            scope.todoChange = todoChange;
            scope.closeThisTodo = closeThisTodo;
            scope.saveTodoText = saveTodoText;
            scope.changeDueDate = changeDueDate;
            scope.saveTodoDueDate = saveTodoDueDate;
            scope.createLabel = createLabel;
            scope.selectLabelComponent = selectLabelComponent;
            scope.saveCreateLabel = saveCreateLabel;
            scope.saveCreateLabelAll = saveCreateLabelAll;
            scope.editLabel = editLabel;
            scope.selectEditLabelComponent = selectEditLabelComponent;
            scope.saveEditLabel = saveEditLabel;
            scope.changeLabel = changeLabel;
            scope.changeTodoLabel = changeTodoLabel;
            scope.deleteEditLabel = deleteEditLabel;
            scope.confirmDeleteLabel = confirmDeleteLabel;
            scope.changeMember = changeMember;
            scope.changeTodoMember = changeTodoMember;
            scope.clickOutSide = clickOutSide;
            scope.removeMember = removeMember;

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

            function isDueDate(date) {
                var date = new Date(date);
                var today = new Date();
                if (date < today) {
                    return 'due-date';
                }
                return '';
            }

            function updateTodoStatus(todo) {
                scope.dragged = true;
                // Don't show confirmation popup if change status from accomplished to true.
                // Because default ui checkbox behaviour the todo's accomplished status will be updated before confirm popup display
                // so we have to used todo's accomplished value changed already in frontend at this point
                if (todo.accomplished && _.contains(sharedService.settings.todo_popup_confirm, scope.activeUser.role)) {
                    let confirmationPopup = ngDialog.open({
                        template: 'todoPopupConfirmDialog',
                        showClose: false,
                        closeByEscape: false,
                        closeByDocument: false,
                        closeByNavigation: false
                    });

                    confirmationPopup.closePromise.then(function (response) {
                        if (response.value) {
                            acceptedChangeTodoStatus();
                        } else {
                            // revert back to original todo's accomplished status due to non customized checkbox
                            todo.accomplished = !todo.accomplished;
                        }
                    })
                } else {
                    acceptedChangeTodoStatus()
                }

                /**
                 * TODO: Decide where to put this updated http services
                 * Callback page scope method
                 */
                function acceptedChangeTodoStatus() {
                    patientService.toggleTodoStatus(todo);
                }
            }

            function open_todo(todo) {
                if (!scope.dragged && !scope.todo_changed) {
                    $location.url('/todo/' + todo.id);
                }
            }

            function todoChange(todo) {
                scope.current_todo = todo;
                currentTodo = todo.todo;
                scope.todo_changed = true;
                todoService.addTodoAccessEncounter(todo.id).then(function () {
                    todo.changed = true;
                });
            }

            function closeThisTodo(todo) {
                if (currentTodo !== undefined)
                    todo.todo = currentTodo;
                todo.changed = false;
                scope.todo_changed = false;
                todo.change_due_date = false;
                todo.change_label = false;
            }

            function saveTodoText(todo) {
                todoService.changeTodoText(todo).then(function (data) {
                    if (data['success']) {
                        toaster.pop('success', "Done", "Updated Todo text!");
                        todo.changed = false;
                        scope.todo_changed = false;

                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }

                });
            }

            function changeDueDate(todo) {
                todo.change_due_date = !todo.change_due_date;
            }

            function saveTodoDueDate(todo) {
                todoService.changeTodoDueDate(todo).then(function (data) {
                    if (data['success']) {
                        if (scope.allowDueDateNotification)
                            toaster.pop('success', "Done", "Due date Updated!");
                        scope.allowDueDateNotification = true;

                    } else if (!data['success']) {
                        todo.due_date = data['todo']['due_date'];
                        toaster.pop('error', 'Error', 'Invalid date format');
                        scope.allowDueDateNotification = false;
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            }

            function createLabel(todo) {
                todo.create_label = !todo.create_label;
            }

            function selectLabelComponent(component) {
                scope.label_component.css_class = component.css_class;
            }

            function saveCreateLabel(todo) {
                scope.label_component.is_all = null;
                if (scope.label_component.css_class !== null) {
                    todoService.saveCreateLabel(todo.id, scope.label_component).then(function (data) {
                        if (data['success']) {
                            if (data['new_status']) {
                                scope.labels.push(data['new_label']);
                            }
                            if (data['status']) {
                                todo.labels.push(data['label']);
                                toaster.pop('success', "Done", "Added Todo label!");
                            }

                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                todo.create_label = false;
            }

            function saveCreateLabelAll(todo) {
                scope.label_component.is_all = true;
                if (scope.label_component.css_class !== null) {
                    todoService.saveCreateLabel(todo.id, scope.label_component).then(function (data) {
                        if (data['success']) {
                            if (data['new_status']) {
                                scope.labels.push(data['new_label']);
                            }
                            if (data['status']) {
                                todo.labels.push(data['label']);
                                toaster.pop('success', "Done", "Added Todo label!");
                            }

                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                todo.create_label = false;
            }

            function editLabel(label) {
                label.edit_label = !label.edit_label;
            }

            function selectEditLabelComponent(label, component) {
                label.css_class = component.css_class;
            }

            function saveEditLabel(label) {
                if (label.css_class != null) {
                    todoService.saveEditLabel(label).then(function (data) {
                        if (data['success']) {
                            label.css_class = data['label']['css_class'];
                            if (data['status']) {
                                angular.forEach(scope.todoList, function (todo, key) {
                                    angular.forEach(todo.labels, function (value, key2) {
                                        if (value.id == label.id) {
                                            value.css_class = label.css_class;
                                        }
                                    });
                                });
                                toaster.pop('success', "Done", "Changed label!");
                            }
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                label.edit_label = false;
            }

            function changeLabel(todo) {
                todo.change_label = !todo.change_label;
            }

            function changeTodoLabel(todo, label) {

                let is_existed = false;
                let existed_key;
                let existed_id;

                angular.forEach(todo.labels, function (value, key) {
                    if (value.name === label.name) {
                        is_existed = true;
                        existed_key = key;
                        existed_id = value.id;
                    }
                });
                if (!is_existed) {
                    todo.labels.push(label);
                    todoService.addTodoLabel(label.id, todo.id).then(function (data) {
                        if (data['success']) {
                            toaster.pop('success', "Done", "Added Todo label!");

                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                } else {
                    todo.labels.splice(existed_key, 1);
                    todoService.removeTodoLabel(existed_id, todo.id).then(function (data) {
                        if (data['success']) {
                            toaster.pop('success', "Done", "Removed Todo label!");
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
            }

            function deleteEditLabel(label) {
                scope.currentLabel = label;
                angular.element('#deleteLabelModal').modal();
            }

            function confirmDeleteLabel(currentLabel) {
                todoService.deleteLabel(currentLabel).then(function (data) {
                    var index = scope.labels.indexOf(currentLabel);
                    scope.labels.splice(index, 1);

                    angular.forEach(scope.todoList, function (todo, key) {
                        var index2;
                        angular.forEach(todo.labels, function (value, key2) {
                            if (value.id == currentLabel.id) {
                                index2 = key2;
                            }
                        });
                        if (index2 != undefined)
                            todo.labels.splice(index2, 1);
                    });

                    angular.element('#deleteLabelModal').modal('hide');
                    toaster.pop('success', 'Done', 'Deleted label successfully');
                });
            }

            function changeMember(todo) {
                todo.change_member = !todo.change_member;
            }

            function changeTodoMember(todo, member) {
                let is_existed = false;
                let existed_key;
                _.each(todo.members, function (value, key) {
                    if (value.id === member.id) {
                        is_existed = true;
                        existed_key = key;
                    }
                });

                if (!is_existed) {
                    todo.members.push(member.user);
                    todoService.addTodoMember(todo, member).then(function (data) {
                        data.success ? toaster.pop('success', "Done", "Added member!") : toaster.pop('error', 'Warning', 'Something went wrong!');
                    });
                } else {
                    todo.members.splice(existed_key, 1);
                    todoService.removeTodoMember(todo, member).then(function (data) {
                        data.success ? toaster.pop('success', "Done", "Removed member!") : toaster.pop('error', 'Warning', 'Something went wrong!');
                    });
                }

            }

            function clickOutSide() {
                if (scope.current_todo != null) {
                    scope.current_todo.changed = false;
                    scope.todo_changed = false;
                    scope.current_todo.change_due_date = false;
                    scope.current_todo.change_label = false;
                    scope.current_todo.change_member = false;
                    scope.current_todo.create_label = false;
                    scope.current_todo = null;
                }
            }

            /**
             *
             * @param todo Reference to value in the todo list
             * @param member
             * @param memberIdx
             */
            function removeMember(todo, member, memberIdx) {
                todo.members.splice(memberIdx, 1);
                todoService.removeTodoMember(todo, member).then((data) => {
                    data.success ? toaster.pop('success', "Done", "Removed member!") : toaster.pop('error', 'Warning', 'Something went wrong!');
                });
            }
        }
    }
})();