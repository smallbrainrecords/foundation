var todos = angular.module('todos', []);

todos.directive('todo', ['patientService', 'toaster', '$location', todoDirective]);

function todoDirective(patientService, toaster, $location) {

    var todoObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/todo.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('todos_ready', function(newVal, oldVal) {
                        if(newVal) {
                            if (scope.todos_ready) {
                                scope.accomplished = scope.$eval(attr.accomplished);

                                scope.problem_todos = scope.$eval(attr.ngModel);
                                var tmpList = scope.problem_todos;
                                scope.sortingLog = [];
                                scope.sorted = false;
                                scope.dragged = false;
                                  
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
                                    }else{
                                        alert("Something went wrong!");
                                    }
                                    scope.dragged = false;
                                });             

                            }

                            scope.open_todo = function(todo) {
                                if (!scope.dragged) {
                                    $location.url('/todo/' + todo.id);
                                }
                            }
                        }
                    }, true);
                }
            }

};
