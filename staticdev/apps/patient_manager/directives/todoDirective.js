var todos = angular.module('todos', []);

todos.directive('todo', ['todoService', 'patientService', 'toaster', '$location', '$timeout', todoDirective]);

function todoDirective(todoService, patientService, toaster, $location, $timeout) {

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
                                scope.current_todo = null;

                                scope.problem_todos = scope.$eval(attr.ngModel);
                                var tmpList = scope.problem_todos;

                                scope.sortingLog = [];
                                scope.sorted = false;
                                scope.dragged = false;

                                // label
                                scope.labels_component = [
                                    {name: 'green', css_class: 'todo-label-green'},
                                    {name: 'yellow', css_class: 'todo-label-yellow'},
                                    {name: 'orange', css_class: 'todo-label-orange'},
                                    {name: 'red', css_class: 'todo-label-red'},
                                    {name: 'purple', css_class: 'todo-label-purple'},
                                    {name: 'blue', css_class: 'todo-label-blue'},
                                    {name: 'sky', css_class: 'todo-label-sky'},
                                ];
                                scope.label_component = {};
                                  
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
                                            form.patient_id = scope.patient_id;

                                            patientService.updateTodoOrder(form).then(function(data){
                                                toaster.pop('success', 'Done', 'Updated Problem');
                                                scope.set_authentication_false();
                                            });
                                        }
                                        scope.sorted = false;
                                        $timeout(function() {
                                            scope.dragged = false;
                                        }, 100);
                                    }
                                }
                                scope.todos_ready = false;
                            }

                            scope.isDueDate = function(date) {
                                var date = new Date(date);
                                var today = new Date();
                                if (date < today) {
                                    return 'due-date';
                                }
                                return '';
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
                                scope.current_todo = todo;
                                currentTodo = todo.todo;
                                scope.todo_changed = true;
                                todoService.addTodoAccessEncounter(todo.id).then(function() {
                                    todo.changed = true;
                                });
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

                            scope.allowDueDateNotification = true;
                            scope.saveTodoDueDate = function(todo) {
                                todoService.changeTodoDueDate(todo).then(function(data){
                                    if(data['success']==true){
                                        if (scope.allowDueDateNotification)
                                            toaster.pop('success', "Done", "Due date Updated!");
                                        scope.allowDueDateNotification = true;
                                        scope.set_authentication_false();
                                    }else if(data['success']==false){
                                        todo.due_date = data['todo']['due_date'];
                                        toaster.pop('error', 'Error', 'Invalid date format');
                                        scope.allowDueDateNotification = false;
                                    }else{
                                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                                    }
                                });
                            }

                            scope.createLabel = function(todo) {
                                todo.create_label = (todo.create_label != true) ? true : false;
                            }

                            scope.selectLabelComponent = function(component) {
                                scope.label_component.css_class = component.css_class;
                            }

                            scope.saveCreateLabel = function(todo) {
                                scope.label_component.is_all = null;
                                if (scope.label_component.css_class != null) {
                                    todoService.saveCreateLabel(todo.id, scope.label_component).then(function(data){
                                        if(data['success']==true){
                                            if(data['new_status']==true){
                                                scope.labels.push(data['new_label']);
                                            }
                                            if(data['status']==true){
                                                todo.labels.push(data['label']);
                                                toaster.pop('success', "Done", "Added Todo label!");
                                            }
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                }
                                todo.create_label = false;
                            }

                            scope.saveCreateLabelAll = function(todo) {
                                scope.label_component.is_all = true;
                                if (scope.label_component.css_class != null) {
                                    todoService.saveCreateLabel(todo.id, scope.label_component).then(function(data){
                                        if(data['success']==true){
                                            if(data['new_status']==true){
                                                scope.labels.push(data['new_label']);
                                            }
                                            if(data['status']==true){
                                                todo.labels.push(data['label']);
                                                toaster.pop('success', "Done", "Added Todo label!");
                                            }
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                }
                                todo.create_label = false;
                            }

                            scope.editLabel = function(label) {
                                label.edit_label = (label.edit_label != true) ? true : false;
                            }

                            scope.selectEditLabelComponent = function(label, component) {
                                label.css_class = component.css_class;
                            }

                            scope.saveEditLabel = function(label) {
                                if (label.css_class != null) {
                                    todoService.saveEditLabel(label).then(function(data){
                                        if(data['success']==true){
                                            label.css_class = data['label']['css_class'];
                                            if(data['status']==true){
                                                angular.forEach(scope.problem_todos, function(todo, key) {
                                                    angular.forEach(todo.labels, function(value, key2) {
                                                        if (value.id == label.id) {
                                                            value.css_class = label.css_class;
                                                        }
                                                    });
                                                });
                                                toaster.pop('success', "Done", "Changed label!");
                                            }
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                }
                                label.edit_label = false;
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
                                    todoService.addTodoLabel(label.id, todo.id).then(function(data){
                                        if(data['success']==true){
                                            toaster.pop('success', "Done", "Added Todo label!");
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                } else {
                                    todo.labels.splice(existed_key, 1);
                                    todoService.removeTodoLabel(existed_id, todo.id).then(function(data){
                                        if(data['success']==true){
                                            toaster.pop('success', "Done", "Removed Todo label!");
                                            scope.set_authentication_false();
                                        }else{
                                            toaster.pop('error', 'Warning', 'Something went wrong!');
                                        }
                                    });
                                }
                                
                            }

                            scope.deleteEditLabel = function(label) {
                                scope.currentLabel = label;
                                angular.element('#deleteLabelModal').modal();
                            }

                            scope.confirmDeleteLabel = function(currentLabel) {
                                todoService.deleteLabel(currentLabel).then(function(data){
                                    var index = scope.labels.indexOf(currentLabel);
                                    scope.labels.splice(index, 1);
                                    
                                    angular.forEach(scope.problem_todos, function(todo, key) {
                                        var index2;
                                        angular.forEach(todo.labels, function(value, key2) {
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

                            scope.clickOutSide = function() {
                                if (scope.current_todo != null) {
                                    scope.current_todo.changed = false;
                                    scope.todo_changed = false;
                                    scope.current_todo.change_due_date = false;
                                    scope.current_todo.change_label = false;
                                    scope.current_todo.change_member = false;
                                    scope.current_todo.create_label = false;
                                    scope.current_todo == null;
                                }
                            }
                        }
                    }, true);
                }
            }

};
