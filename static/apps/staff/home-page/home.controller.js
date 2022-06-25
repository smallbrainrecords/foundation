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


    angular.module('StaffApp')
        .controller('HomeCtrl', function ($scope, $routeParams, $interval,
            ngDialog, toaster, prompt,
            staffService, physicianService, todoService, sharedService) {

            // Properties
            // $scope.user_id = $('#user_id').val();
            $scope.taggedTodoCollapsed = false;
            $scope.lastTimeTaggedTodoAccessed = null;
            $scope.showAccomplishedTaggedTodos = false;
            $scope.newTaggedTodo = 0;
            $scope.todos_ready = false;

            // $scope.users = [];
            $scope.new_list = {};
            $scope.new_list.labels = [];
            $scope.todo_lists = [];
            $scope.currentLabel = null;
            $scope.active_user = null;
            $scope.show_all = false;
            $scope.show_accomplished_personal_todos = false;
            $scope.showLabeledTodoList = false;
            $scope.reverse = false;
            $scope.pendingUsers = [];

            $scope.sortingKey = "";
            $scope.isDescending = true;

            // Function definitions
            $scope.openTaggedTodo = openTaggedTodo;
            $scope.closeTaggedTodo = closeTaggedTodo;
            $scope.add_todo = add_todo;
            $scope.add_new_list_label = add_new_list_label;
            $scope.add_todo_list = add_todo_list;
            $scope.delete_list = delete_list;
            $scope.refresh_todos_physicians = refresh_todos_physicians;
            $scope.orderByDate = orderByDate;
            $scope.getNewTodos = getNewTodos;
            $scope.openTodoList = openTodoList;
            $scope.sortBy = sortBy;
            $scope.refreshPendingUsers = refreshPendingUsers;
            $scope.updatePendingUser = updatePendingUser;

            init();

            function init() {
                staffService.getPatientsList().then(function (data) {
                    $scope.patients_list = data['patients_list'];
                });

                staffService.fetchActiveUser().then(function (data) {

                    $scope.active_user = data['user_profile'];
                    $scope.lastTimeTaggedTodoAccessed = $scope.active_user.last_access_tagged_todo;

                    var role_form = {

                        'actor_role': $scope.active_user.role,
                        'actor_id': $scope.active_user.user.id
                    };

                    if ($scope.active_user.role == 'physician') {
                        // physicianService.getUsersList(role_form).then(function (data) {
                        //     $scope.users = data;
                        // });

                        var form = { 'physician_id': $scope.active_user.user.id };
                        physicianService.getPhysicianTeam(form).then(function (data) {
                            $scope.team = data;
                        });
                    }

                    // Refresh new todo for secretary
                    if ($scope.active_user.role == 'secretary') {
                        $scope.refresh_todos_physicians();
                        $interval(function () {
                            $scope.refresh_todos_physicians();
                        }, 10000);
                    }

                    if ($scope.active_user.role == 'secretary' || $scope.active_user.role == 'mid-level' || $scope.active_user.role == 'nurse') {
                        staffService.getAllTodos($scope.user_id).then(function (data) {
                            $scope.all_todos_list = data['all_todos_list'];
                        });
                    }

                });

                staffService.getUserTodoList($scope.user_id).then(function (data) {
                    $scope.tagged_todos = data['tagged_todos'];
                    $scope.personal_todos = data['personal_todos'];
                    $scope.newTaggedTodo = data['new_tagged_todo'];
                    $scope.todos_ready = true;
                });

                todoService.fetchLabels($scope.user_id).then(function (data) {
                    $scope.labels = data['labels'];
                });

                staffService.fetchLabeledTodoList($scope.user_id).then(function (data) {
                    $scope.todo_lists = data['todo_lists'];
                });

                $scope.refreshPendingUsers();
            }

            /**
             *
             * @param form
             */
            function add_todo(form) {
                if (form == undefined || form.name.trim().length < 1) {
                    return false;
                }

                form.user_id = $scope.user_id;

                askDueDate();

                function askDueDate() {
                    var acceptedFormat = ['MM/DD/YYYY', "M/D/YYYY", "MM/YYYY", "M/YYYY", "MM/DD/YY", "M/D/YY", "MM/YY", "M/YY"];

                    var dueDateDialog = ngDialog.open({
                        template: 'askDueDateDialog',
                        showClose: false,
                        closeByDocument: false,
                        closeByNavigation: false,
                        controller: function () {
                            var vm = this;
                            vm.dueDate = '';
                            vm.dueDateIsValid = function () {
                                var isValid = moment(vm.dueDate, acceptedFormat, true).isValid();
                                if (!isValid)
                                    toaster.pop('error', 'Error', 'Please enter a valid date!');
                                return isValid;
                            };
                        },
                        controllerAs: 'vm'
                    });

                    dueDateDialog.closePromise.then(function (data) {
                        if (!_.isUndefined(data.value) && '$escape' != data.value)
                            form.due_date = moment(data.value, acceptedFormat).toString();
                        staffService.addToDo(form).then(addTodoSuccess);
                    })
                }

                function addTodoSuccess(data) {

                    var new_todo = data['todo'];
                    $scope.personal_todos.push(new_todo);
                    $scope.new_todo = {};
                    toaster.pop('success', 'Done', 'Added Todo!');

                }
            }

            /**
             *
             * @param new_list
             * @param label
             */
            function add_new_list_label(new_list, label) {
                var index = new_list.labels.indexOf(label);
                if (index > -1)
                    new_list.labels.splice(index, 1);
                else
                    new_list.labels.push(label);
            }

            /***
             *
             * @param form
             * @param visibility
             */
            function add_todo_list(form, visibility) {
                form.user_id = $scope.user_id;
                form.visibility = visibility;
                if (form.name && form.labels.length > 0) {
                    staffService.addToDoList(form)
                        .then(function (data) {
                            if (data.success) {

                                var new_list = data['new_list'];
                                $scope.todo_lists.push(new_list);
                                $scope.new_list = {};
                                $scope.new_list.labels = [];
                                toaster.pop('success', 'Done', 'New to do list added successfully');
                            } else {
                                toaster.pop('error', 'Error', "You don't have permission to do this action");
                            }
                        }, function (data) {
                            toaster.pop('error', 'Error', "Something when wrong, We fix this ASAP");

                        });
                } else {
                    toaster.pop('error', 'Error', 'Please select name and labels');
                }
            }

            /**
             *
             * @param list
             */
            function delete_list(list) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a todo list is forever. There is no undo."
                }).then(function (result) {
                    staffService.deleteToDoList(list)
                        .then(function (data) {
                            if (data.success) {
                                var index = $scope.todo_lists.indexOf(list);
                                $scope.todo_lists.splice(index, 1);
                                toaster.pop('success', 'Done', 'To do list removed successfully');
                            } else {
                                toaster.pop('error', 'Error', "You don't have permission to delete");
                            }
                        });
                }, function () {
                    return false;
                });
            }

            /**
             *
             */
            function refresh_todos_physicians() {
                staffService.getTodosPhysicians($scope.user_id).then(function (data) {
                    $scope.new_generated_todos_list = data['new_generated_todos_list'];
                    $scope.new_generated_physicians_list = data['new_generated_physicians_list'];
                })
            }

            /**
             *
             * @param item
             * @returns {number}
             */
            function orderByDate(item) {
                if (item.due_date != null) {
                    var parts = item.due_date.split('/');
                    var number = parseInt(parts[2] + parts[0] + parts[1]);
                } else {
                    var number = 0;
                }

                return -number;
            }

            /**
             *
             * @param list
             * @returns {number}
             */
            function getNewTodos(list) {
                var number = 0;
                angular.forEach(list.todos, function (value, key) {
                    if (list.expanded.indexOf(value.id) == -1) {
                        number += 1;
                    }
                });

                return number;
            }

            /**
             *
             * @param list
             */
            function openTodoList(list) {
                list.collapse = !list.collapse;
                if (list.collapse) {
                    var form = {};
                    form.list_id = list.id;
                    form.todos = list.todos;

                    var is_existed = false;
                    angular.forEach(list.todos, function (value, key) {
                        if (list.expanded.indexOf(value.id) == -1) {
                            list.expanded.push(value.id);
                            is_existed = true;
                        }
                    });

                    if (is_existed) {
                        staffService.openTodoList(form).then(function (data) {
                        });
                    }
                }
            }

            function openTaggedTodo() {
                $scope.taggedTodoCollapsed = false;

                staffService.updateLastTimeAccessTaggedTodo($scope.user_id).then(function (response) {
                    $scope.lastTimeTaggedTodoAccessed = new Date();
                });
            }

            function closeTaggedTodo() {
                $scope.taggedTodoCollapsed = true;
            }

            function sortBy(sortKey) {
                // If sorting same column then reverse the sorting order, otherwise set default sorting order is descending
                $scope.isDescending = (_.isEqual($scope.sortingKey, sortKey)) ? !$scope.isDescending : true;
                // Update sorting key
                $scope.sortingKey = sortKey;
                staffService.getTopPatientList($scope.sortingKey, $scope.isDescending)
                    .then(function (data) {
                        $scope.patients_list = data['patients_list'];
                    });
            }

            function refreshPendingUsers() {
                sharedService.getPendingRegistrationUsersList().then(function (data) {
                    $scope.pendingUsers = data;
                });
            }

            function updatePendingUser(user, status) {
                switch (status) {
                    case 1: // Approve
                        if (user.role == 'patient') {
                            sharedService.approveUser(user).then(userUpdateSucceed);
                        } else {
                            alert("Please assign role!");
                        }
                        break;
                    case 0: // Reject
                        sharedService.rejectUser(user).then(userUpdateSucceed);
                        break;
                }

                function userUpdateSucceed() {
                    let index = $scope.pendingUsers.indexOf(user);
                    if (index > -1) {
                        $scope.pendingUsers.splice(index, 1);
                    }
                }
            }
        });
    /* End of controller */


})();