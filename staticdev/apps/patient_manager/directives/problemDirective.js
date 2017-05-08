var problems = angular.module('problems', []).config(function($httpProvider){
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    });

problems.directive('problem', ['problemService', 'patientService', 'toaster', '$location', '$timeout', problemDirective]);

function problemDirective(problemService, patientService, toaster, $location, $timeout) {

    var todoObj = {}; 

            return {
                restrict: 'E',
                templateUrl: '/static/apps/patient_manager/directives/templates/problem.html',
                scope: true,
                link: function (scope, element, attr, model) {
                    scope.$watch('problems_ready', function(newVal, oldVal) {
                        if(newVal) {

                            scope.is_list = scope.$eval(attr.isList);
                            scope.problems = scope.$eval(attr.ngModel);

                            if (scope.problems_ready) {
                                var tmpListProblemList = scope.problems;

                                scope.sortingLogProblemList = [];
                                scope.sortedProblemList = false;
                                scope.draggedProblemList = false;
                                scope.sortableOptionsProblemList = {
                                    update: function(e, ui) {
                                        scope.sortedProblemList = true;
                                    },
                                    start: function() {
                                        scope.draggedProblemList = true;
                                    },
                                    stop: function(e, ui) {
                                        // this callback has the changed model
                                        if (scope.sortedProblemList) {
                                            scope.sortingLogProblemList = [];
                                            tmpListProblemList.map(function(i){
                                                scope.sortingLogProblemList.push(i.id);
                                            });
                                            var form = {};

                                            form.problems = scope.sortingLogProblemList;
                                            
                                            if (scope.is_list) {
                                                form.list_id = scope.is_list;
                                            } else {
                                                form.patient_id = scope.patient_id;
                                            }

                                            patientService.updateProblemOrder(form).then(function(data){
                                                toaster.pop('success', 'Done', 'Updated Problem Order');
                                            });
                                        }
                                        scope.sortedProblem = false;
                                        $timeout(function() {
                                            scope.draggedProblemList = false;
                                        }, 100);
                                    }
                                }
                                scope.problems_ready = false;
                            }

                            scope.open_problem = function(problem){
                                if (!scope.draggedProblemList) {
                                    $location.path('/problem/'+problem.id);
                                }
                            };
                        }
                    }, true);
                }
            }

};
