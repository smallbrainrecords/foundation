(function () {

    'use strict';


    angular.module('StaffApp')
        .controller('HomeCtrl', function ($scope, $routeParams, ngDialog,
                                          staffService, physicianService, toaster, todoService, prompt, $interval) {


            $scope.init = function () {
                var user_id = $('#user_id').val();
                $scope.user_id = user_id;

                staffService.getPatientsList().then(function (data) {
                    $scope.patients_list = data['patients_list'];
                });


                $scope.users = [];
                $scope.new_list = {};
                $scope.new_list.labels = [];
                $scope.todo_lists = [];
                $scope.currentLabel = null;


                staffService.fetchActiveUser().then(function (data) {

                    $scope.active_user = data['user_profile'];

                    var role_form = {

                        'actor_role': $scope.active_user.role,
                        'actor_id': $scope.active_user.user.id
                    };

                    if ($scope.active_user.role == 'physician') {
                        physicianService.getUsersList(role_form).then(function (data) {
                            $scope.users = data;
                        });

                        var form = {'physician_id': $scope.active_user.user.id};
                        physicianService.getPhysicianData(form).then(function (data) {

                            $scope.patients = data['patients'];
                            $scope.team = data['team'];

                        });
                    }

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

                staffService.getUserTodoList(user_id).then(function (data) {
                    $scope.tagged_todos = data['tagged_todos'];
                    $scope.personal_todos = data['personal_todos'];
                    $scope.todos_ready = true;
                });

                todoService.fetchTodoMembers($scope.user_id).then(function (data) {
                    $scope.members = data['members'];
                });

                todoService.fetchLabels($scope.user_id).then(function (data) {
                    $scope.labels = data['labels'];
                });

                staffService.fetchLabeledTodoList($scope.user_id).then(function (data) {
                    $scope.todo_lists = data['todo_lists'];
                });
            };

            $scope.add_todo = function (form) {

                form.user_id = $scope.user_id;

                prompt({
                    title: 'Add Due Date',
                    message: 'Enter due date',
                    input: true,
                    label: 'Due Date'
                }).then(function (due_date) {
                    if (moment(due_date, "MM/DD/YYYY", true).isValid()) {
                        form.due_date = due_date;
                    } else if (moment(due_date, "M/D/YYYY", true).isValid()) {
                        form.due_date = moment(due_date, "M/D/YYYY").format("MM/DD/YYYY");
                    } else if (moment(due_date, "MM/YYYY", true).isValid()) {
                        form.due_date = moment(due_date, "MM/YYYY").date(1).format("MM/DD/YYYY");
                    } else if (moment(due_date, "M/YYYY", true).isValid()) {
                        form.due_date = moment(due_date, "M/YYYY").date(1).format("MM/DD/YYYY");
                    } else if (moment(due_date, "MM/DD/YY", true).isValid()) {
                        form.due_date = moment(due_date, "MM/DD/YY").format("MM/DD/YYYY");
                    } else if (moment(due_date, "M/D/YY", true).isValid()) {
                        form.due_date = moment(due_date, "M/D/YY").format("MM/DD/YYYY");
                    } else if (moment(due_date, "MM/YY", true).isValid()) {
                        form.due_date = moment(due_date, "MM/YY").date(1).format("MM/DD/YYYY");
                    } else if (moment(due_date, "M/YY", true).isValid()) {
                        form.due_date = moment(due_date, "M/YY").date(1).format("MM/DD/YYYY");
                    } else {
                        toaster.pop('error', 'Error', 'Please enter a valid date!');
                        return false;
                    }

                    staffService.addToDo(form).then(function (data) {
                        var new_todo = data['todo'];
                        $scope.personal_todos.push(new_todo);
                        $scope.new_todo = {};
                        toaster.pop('success', 'Done', 'New Todo added successfully');
                    });
                }, function () {
                    staffService.addToDo(form).then(function (data) {
                        var new_todo = data['todo'];
                        $scope.personal_todos.push(new_todo);
                        $scope.new_todo = {};
                        toaster.pop('success', 'Done', 'New Todo added successfully');
                    });
                });
            };

            $scope.add_new_list_label = function (new_list, label) {
                var index = new_list.labels.indexOf(label);
                if (index > -1)
                    new_list.labels.splice(index, 1);
                else
                    new_list.labels.push(label);
            };

            $scope.add_todo_list = function (form) {

                form.user_id = $scope.user_id;
                if (form.name && form.labels.length > 0) {
                    staffService.addToDoList(form).then(function (data) {
                        var new_list = data['new_list'];
                        $scope.todo_lists.push(new_list);
                        $scope.new_list = {};
                        $scope.new_list.labels = [];
                        toaster.pop('success', 'Done', 'New Todo List added successfully');
                    });
                } else {
                    toaster.pop('error', 'Error', 'Please select name and labels');
                }
            };

            $scope.delete_list = function (list) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a todo list is forever. There is no undo."
                }).then(function (result) {
                    staffService.deleteToDoList(list).then(function (data) {
                        var index = $scope.todo_lists.indexOf(list);
                        $scope.todo_lists.splice(index, 1);
                        toaster.pop('success', 'Done', 'Todo List removed successfully');
                    });
                }, function () {
                    return false;
                });
            };

            $scope.refresh_todos_physicians = function () {
                staffService.getTodosPhysicians($scope.user_id).then(function (data) {
                    $scope.new_generated_todos_list = data['new_generated_todos_list'];
                    $scope.new_generated_physicians_list = data['new_generated_physicians_list'];
                })
            };

            $scope.orderByDate = function (item) {
                if (item.due_date != null) {
                    var parts = item.due_date.split('/');
                    var number = parseInt(parts[2] + parts[0] + parts[1]);
                } else {
                    var number = 0;
                }

                return -number;
            };

            $scope.getNewTodos = function (list) {
                var number = 0;
                angular.forEach(list.todos, function (value, key) {
                    if (list.expanded.indexOf(value.id) == -1) {
                        number += 1;
                    }
                });

                return number;
            };

            $scope.openTodoList = function (list) {
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
            };


            $scope.init();

        });
    /* End of controller */


})();