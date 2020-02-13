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
var problems = angular.module('problems', []).config(function ($httpProvider) {
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
});

problems.directive('problem', ['problemService', 'patientService', 'toaster', '$location', '$timeout', problemDirective]);

function problemDirective(problemService, patientService, toaster, $location, $timeout) {

    var todoObj = {};

    return {
        restrict: 'E',
        templateUrl: '/static/apps/patient/directives/templates/problem.html',
        scope: true,
        link: function (scope, element, attr, model) {
            scope.$watch('problems_ready', function (newVal, oldVal) {
                if (newVal) {

                    scope.is_list = scope.$eval(attr.isList);
                    scope.problems = scope.$eval(attr.ngModel);

                    if (scope.problems_ready) {
                        var tmpListProblemList = scope.problems;

                        scope.sortingLogProblemList = [];
                        scope.sortedProblemList = false;
                        scope.draggedProblemList = false;
                        scope.sortableOptionsProblemList = {
                            update: function (e, ui) {
                                scope.sortedProblemList = true;
                            },
                            start: function () {
                                scope.draggedProblemList = true;
                            },
                            stop: function (e, ui) {
                                // this callback has the changed model
                                if (scope.sortedProblemList) {
                                    scope.sortingLogProblemList = [];
                                    tmpListProblemList.map(function (i) {
                                        scope.sortingLogProblemList.push(i.id);
                                    });
                                    var form = {};

                                    form.problems = scope.sortingLogProblemList;

                                    if (scope.is_list) {
                                        form.list_id = scope.is_list;
                                    } else {
                                        form.patient_id = scope.patient_id;
                                    }

                                    patientService.updateProblemOrder(form).then(function (data) {
                                        toaster.pop('success', 'Done', 'Updated Problem Order');
                                    });
                                }
                                scope.sortedProblem = false;
                                $timeout(function () {
                                    scope.draggedProblemList = false;
                                }, 100);
                            }
                        };
                        scope.problems_ready = false;
                    }

                    scope.open_problem = function (problem) {
                        if (!scope.draggedProblemList) {
                            $location.path('/problem/' + problem.id);
                        }
                    };
                }
            }, true);
        }
    }

}
