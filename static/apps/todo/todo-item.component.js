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
        .directive('todoItem', TodoItem);

    TodoItem.$inject = ['todoService', 'patientService', 'toaster', '$location', '$timeout', 'sharedService', 'ngDialog', 'LABELS'];

    function TodoItem(todoService, patientService, toaster, $location, $timeout, sharedService, ngDialog, LABELS) {
        return {
            restrict: 'E',
            templateUrl: '/static/apps/todo/todo-item.template.html',
            scope: {
                item: "=",
                showProblem: '=',
                patientId: "=", // Migrate to data service
                userId: "=", // Migrate to data service
                activeUser: "=",
                labels: "=",
                members: "=",
                editStarted: "=",
                editFinished: "=",
            },
            link: linkFn
        };

        function linkFn(scope, element, attr, model) {
            scope.editMode = false;
            scope.allowDueDateNotification = true;
            scope.current_todo = null; // Holding temporary copy of todo item for editing
            scope.labels_component = LABELS;
            scope.label_component = {};

            scope.openTodo = openTodo;

            scope.enableEditMode = enableEditMode;

            scope.updateTodoStatus = updateTodoStatus;

            scope.saveTodoText = saveTodoText;

            scope.isDueDate = isDueDate;
            scope.changeDueDate = changeDueDate;
            scope.saveTodoDueDate = saveTodoDueDate;

            scope.editLabel = editLabel;
            scope.selectLabelComponent = selectLabelComponent;
            scope.createLabel = createLabel;
            scope.saveCreateLabel = saveCreateLabel;
            scope.selectEditLabelComponent = selectEditLabelComponent;
            scope.saveEditLabel = saveEditLabel;
            scope.changeLabel = changeLabel;
            scope.changeTodoLabel = changeTodoLabel;
            scope.deleteEditLabel = deleteEditLabel;
            scope.confirmDeleteLabel = confirmDeleteLabel;

            scope.changeTodoMember = changeTodoMember;
            scope.changeMember = changeMember;
            scope.removeMember = removeMember;

            scope.clickOutSide = finishEditMode;
            // scope.closeThisTodo = closeThisTodo;

            init();

            function init() {
            }

            /**
             * Enable editing mode
             */
            function enableEditMode() {
                scope.editMode = true;

                // Copy todo item for editing to isolate effect to same reference in other list
                scope.current_todo = angular.copy(scope.item);

                // Notify parent
                scope.editStarted();

                // Update tracking API
                todoService.addTodoAccessEncounter(scope.item.id);
            }

            /**
             * Go to todo item detail page
             * @param todo
             */
            function openTodo(todo) {
                $location.url(`/todo/${todo.id}`);
            }


            /**
             * Check if current data is after params date
             * @param date Valid moment date format
             * @returns {string}
             */
            function isDueDate(date) {
                return moment().isAfter(moment(date, 'MM-DD-YYYY')) ? 'due-date' : '';
            }

            /**
             * Toggle todo accomplished status
             * @param todo
             */
            function updateTodoStatus(todo) {
                // Don't show confirmation popup if change status from accomplished to true.
                // Because default ui checkbox behaviour the todo's accomplished status will be updated before confirm popup display
                // so we have to used todo's accomplished value changed already in frontend at this point
                if (todo.accomplished && _.contains(sharedService.settings.todo_popup_confirm, scope.activeUser.role)) {
                    ngDialog.open({
                        template: 'todoPopupConfirmDialog',
                        showClose: false,
                        closeByEscape: false,
                        closeByDocument: false,
                        closeByNavigation: false
                    }).closePromise.then(function (response) {
                        if (response.value) {
                            acceptedChangeTodoStatus();
                        } else {
                            todo.accomplished = !todo.accomplished;
                        }
                    })
                } else {
                    acceptedChangeTodoStatus()
                }

                function acceptedChangeTodoStatus() {
                    patientService.toggleTodoStatus(todo);
                }
            }

            /**
             * Update todo item name
             * @param todo : Temporary
             */
            function saveTodoText(todo) {
                // View
                finishEditMode();

                // Service & Model
                todoService.changeTodoText(todo)
                    .then((data) => {
                        // Display notify message
                        data.success ? toaster.pop('success', "Done", "Updated Todo text!") : toaster.pop('error', 'Warning', 'Something went wrong!');
                    });
            }

            /**
             * Enable edit due date mode
             * @param todo : Temporary copy
             */
            function changeDueDate(todo) {
                todo.change_due_date = !todo.change_due_date;
            }

            /**
             * Update todo due date
             * @param todo: Temporary copy of editing todo item
             */
            function saveTodoDueDate(todo) {
                debugger;
                // Calling API
                todoService.changeTodoDueDate(todo).then((data) => {
                    data.success ? toaster.pop('success', "Done", "Due date Updated!") : toaster.pop('error', 'Error', 'Invalid date format');
                });
            }

            /**
             * Enable create new label mode
             * @param todo
             */
            function createLabel(todo) {
                todo.create_label = !todo.create_label;
            }

            /**
             *
             * @param component
             */
            function selectLabelComponent(component) {
                scope.label_component.css_class = component.css_class;
            }

            /**
             * Save newly created label as private
             * @param todo
             * @param isPrivate
             */
            function saveCreateLabel(todo, isPrivate = null) {
                scope.label_component.is_all = isPrivate;
                if (scope.label_component.css_class !== null) {
                    todoService.saveCreateLabel(todo.id, scope.label_component).then((data) => {
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

            /**
             * Enable label editing mode
             * @param label
             */
            function editLabel(label) {
                label.edit_label = !label.edit_label;
            }

            /**
             *
             * @param label
             * @param component
             */
            function selectEditLabelComponent(label, component) {
                label.css_class = component.css_class;
            }

            /**
             * Update label
             * WIP: Todo's label itself is not being updated
             * @param label
             */
            function saveEditLabel(label) {
                if (label.css_class != null) {
                    todoService.saveEditLabel(label).then((data) => {
                        if (data.success) {
                            label = data.label;

                            patientService.updateTodoLabel(data.label);

                            scope.current_todo = angular.copy(scope.item);

                            toaster.pop('success', "Done", "Changed label!");
                        } else {

                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                label.edit_label = false;
            }

            /**
             * Toggle todo item label editing function
             * @param todo Temporary copy of todo item being edited
             */
            function changeLabel(todo) {
                todo.change_label = !todo.change_label;
            }

            /**
             * Adding or remove todo's label(s)
             * @param todo Temporary copy of editing todo item
             * @param label
             */
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
                        data.success ? toaster.pop('success', "Done", "Added Todo label!") : toaster.pop('error', 'Warning', 'Something went wrong!');
                    });
                } else {
                    todo.labels.splice(existed_key, 1);
                    todoService.removeTodoLabel(existed_id, todo.id).then(function (data) {
                        data.success ? toaster.pop('success', "Done", "Removed Todo label!") : toaster.pop('error', 'Warning', 'Something went wrong!');
                    });
                }
            }

            /**
             * Display label editing prompt
             * @param label
             */
            function deleteEditLabel(label) {
                scope.currentLabel = label;
                scope.deleteDialog = ngDialog.open({
                    template: 'labelDeleteConfirmationDialog',
                    scope: scope
                });
            }

            /**
             * Close the delete model after click the item
             * @param currentLabel
             */
            function confirmDeleteLabel(currentLabel) {
                scope.deleteDialog.close();

                todoService.deleteLabel(currentLabel).then((data) => {
                    // Remove in scope label list (data receive from parent Later migrate to shared service)
                    let index = scope.labels.indexOf(currentLabel);
                    scope.labels.splice(index, 1);

                    // Update global label definition
                    patientService.updateTodoLabel(currentLabel, true);

                    scope.current_todo = angular.copy(scope.item);

                    if (data.success)
                        toaster.pop('success', 'Done', 'Deleted label successfully');
                });
            }

            /**
             * Enable tagged member editing mode
             * @param todo
             */
            function changeMember(todo) {
                todo.change_member = !todo.change_member;
            }

            /**
             *
             * @param todo Temporary copy of editing todo item
             * @param member
             */
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

            /**
             * Done todo editing
             */
            function finishEditMode() {
                // Delegate synchronize task to global service
                patientService.updateTodoCallback(scope.current_todo);

                // Notify parent
                scope.editFinished();

                // Update directive view controller
                scope.editMode = false;
                scope.current_todo = null;

            }

            /**
             * Removing a tagged member by click into there name in todo tagged member list
             * Current directive (later call it component) update the references directly so the other will be affect also
             * Another option is delegate work to separated patient service to unify data workflow. Need thinking
             * @param todo: Reference to unify data source so no need to update after service finished the work
             * @param member
             * @param memberIdx
             */
            function removeMember(todo, member, memberIdx) {
                // Doing view stuff
                todo.members.splice(memberIdx, 1);

                // Delegate to service to handle detail work and synch other usage
                todoService.removeTodoMember(todo, member).then((data) => {
                    data.success ? toaster.pop('success', "Done", "Removed member!") : toaster.pop('error', 'Error', 'Failed to remove member!');
                });
            }
        }
    }
})();