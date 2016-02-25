var todos = angular.module('todos', []);

todos.directive('todo', ['todoService', 'patientService', 'toaster', '$location', todoDirective]);

function todoDirective(todoService, patientService, toaster, $location) {

    var todoObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/todo.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('todos_ready', function(newVal, oldVal) {
                        if(newVal) {
                            scope.set_authentication_false = function() {
                                if (scope.problem) {
                                    if(scope.active_user.role != "physician" && scope.active_user.role != "admin")
                                        scope.problem.authenticated = false;
                                }
                            }

                            if (scope.todos_ready) {
                                var currentTodo;
                                scope.accomplished = scope.$eval(attr.accomplished);
                                scope.show_problem = scope.$eval(attr.showProblem);

                                scope.problem_todos = scope.$eval(attr.ngModel);
                                var tmpList = scope.problem_todos;

                                scope.sortingLog = [];
                                scope.sorted = false;
                                scope.dragged = false;

                                // label
                                scope.labels = [
                                    {name: 'green', css_class: 'todo-label-green'},
                                    {name: 'yellow', css_class: 'todo-label-yellow'},
                                    {name: 'orange', css_class: 'todo-label-orange'},
                                    {name: 'red', css_class: 'todo-label-red'},
                                    {name: 'purple', css_class: 'todo-label-purple'},
                                    {name: 'blue', css_class: 'todo-label-blue'},
                                    {name: 'sky', css_class: 'todo-label-sky'},
                                ];
                                  
                                scope.sortableOptions = {
                                    update: function(e, ui) {
                                        scope.sorted = true;
                                    },
                                    start: function() {
                                        scope.dragged = true;
                                    },
                                    stop: function(e, ui) {
                                        // this callback has the changed model
                                        if (scope.sorted) {
                                            scope.sortingLog = [];
                                            tmpList.map(function(i){
                                                scope.sortingLog.push(i.id);
                                            });
                                            var form = {};

                                            form.todos = scope.sortingLog;

                                            patientService.updateTodoOrder(form).then(function(data){
                                                toaster.pop('success', 'Done', 'Updated Problem');
                                                scope.dragged = false;
                                                scope.set_authentication_false();
                                            });
                                        }
                                        scope.sorted = false;
                                    }
                                }
                                scope.todos_ready = false;
                            }


                            // update status
                            scope.update_todo_status = function(todo){
                                scope.dragged = true;
                                patientService.updateTodoStatus(todo).then(function(data){
                                    if(data['success']==true){
                                        toaster.pop('success', "Done", "Updated Todo status !");
                                        scope.set_authentication_false();
                                    }else{
                                        toaster.pop('error', 'Warning', 'Something went wrong!');
                                    }
                                    scope.dragged = false;
                                });             

                            }

                            scope.open_todo = function(todo) {
                                if (!scope.dragged && !scope.todo_changed) {
                                    $location.url('/todo/' + todo.id);
                                }
                            }

                            scope.todoChange = function(todo) {
                                currentTodo = todo.todo;
                                todo.changed = true;
                                scope.todo_changed = true;
                            }

                            scope.closeThisTodo = function(todo) {
                                if (currentTodo != undefined)
                                    todo.todo = currentTodo;
                                todo.changed = false;
                                scope.todo_changed = false;
                                todo.change_due_date = false;
                                todo.change_label = false;
                            }

                            scope.saveTodoText = function(todo) {
                                todoService.changeTodoText(todo).then(function(data){
                                    if(data['success']==true){
                                        toaster.pop('success', "Done", "Updated Todo text!");
                                        todo.changed = false;
                                        scope.todo_changed = false;
                                        scope.set_authentication_false();
                                    }else{
                                        toaster.pop('error', 'Warning', 'Something went wrong!');
                                    }
                                    
                                });
                            }

                            scope.changeDueDate = function(todo) {
                                todo.change_due_date = (todo.change_due_date != true) ? true : false;
                            }

                            scope.saveTodoDueDate = function(todo) {
                                todoService.changeTodoDueDate(todo).then(function(data){
                                    scope.set_authentication_false();
                                });
                            }

                            scope.changeLabel = function(todo) {
                                todo.change_label = (todo.change_label != true) ? true : false;
                            }

                            scope.changeTodoLabel = function(todo, label) {

                                var is_existed = false;
                                var existed_key;
                                var existed_id;

                                angular.forEach(todo.labels, function(value, key) {
                                    if (value.name==label.name) {
                                        is_existed = true;
                                        existed_key = key;
                                        existed_id = value.id;
                                    }
                                });
                                if (!is_existed) {
                                    todo.labels.push(label);
                                    todo.label_name = label.name;
                                    todo.label_css_class = label.css_class;
                                    todoService.addTodoLabel(todo).then(function(data){
                                        if(data['success']==true){
                                            toaster.pop('success', "Done", "Added Todo label!");
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                } else {
                                    todo.labels.splice(existed_key, 1);
                                    todoService.removeTodoLabel(existed_id).then(function(data){
                                        if(data['success']==true){
                                            toaster.pop('success', "Done", "Removed Todo label!");
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                }
                                
                            }

                            scope.changeMember = function(todo) {
                                todo.change_member = (todo.change_member != true) ? true : false;
                            }

                            scope.changeTodoMember = function(todo, member) {

                                var is_existed = false;
                                var existed_key;
                                var existed_id;

                                angular.forEach(todo.members, function(value, key) {
                                    if (value.id==member.id) {
                                        is_existed = true;
                                        existed_key = key;
                                        existed_id = value.id;
                                    }
                                });
                                if (!is_existed) {
                                    todo.members.push(member);
                                    todoService.addTodoMember(todo, member).then(function(data){
                                        if(data['success']==true){
                                            toaster.pop('success', "Done", "Added member!");
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                } else {
                                    todo.members.splice(existed_key, 1);
                                    todoService.removeTodoMember(todo, member).then(function(data){
                                        if(data['success']==true){
                                            toaster.pop('success', "Done", "Removed member!");
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                }
                                
                            }
                        }
                    }, true);
                }
            }

};
