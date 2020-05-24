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
        .controller('ManageCommonProblemCtrl', function (
            $scope, $routeParams, ngDialog,
            staffService, $location, $anchorScroll, toaster) {

            $scope.chronic_problem_terms = [];
            $scope.acute_problem_terms = [];
            $scope.new_chronic_problem = {set: false};
            $scope.new_acute_problem = {set: false};
            $scope.ready = false;
            $scope.problems = [];

            staffService.fetchActiveUser().then(function (response) {
                let data = response.data;
                $scope.active_user = data['user_profile'];
                $scope.ready = true;

                staffService.getCommonProblems($scope.active_user.user.id).then(function (response) {
                    let data = response.data;
                    $scope.problems = data['problems'];
                });
            });


            $scope.$watch('chronic_problem', function (newVal, oldVal) {

                console.log(newVal);
                if (newVal === undefined) {
                    return false;
                }

                $scope.unset_new_problem($scope.new_chronic_problem);

                if (newVal.length > 2) {
                    staffService.listTerms(newVal).then(function (response) {
                        let data = response.data;
                        $scope.chronic_problem_terms = data;
                    });
                } else {
                    $scope.chronic_problem_terms = [];

                }
            });

            $scope.$watch('acute_problem', function (newVal, oldVal) {

                if (newVal === undefined) {
                    return false;
                }

                $scope.unset_new_problem($scope.new_acute_problem);

                if (newVal.length > 2) {
                    staffService.listTerms(newVal).then(function (response) {
                        let data = response.data;
                        $scope.acute_problem_terms = data;
                    });
                } else {
                    $scope.acute_problem_terms = [];

                }
            });


            $scope.set_new_problem = function (new_problem, problem) {
                new_problem.set = true;
                new_problem.active = problem.active;
                new_problem.term = problem.term;
                new_problem.code = problem.code;
            };


            $scope.unset_new_problem = function (new_problem) {
                new_problem.set = false;
            };


            $scope.add_problem = function (new_problem, type) {

                var c = confirm("Are you sure?");

                if (c === false) {
                    return false;
                }

                var form = {};
                form.staff_id = $scope.active_user.user.id;
                form.problem_name = new_problem.term;
                form.concept_id = new_problem.code;
                form.problem_type = type;
                form.active = new_problem.active;

                staffService.addCommonProblem(form).then(function (response) {
                    let data = response.data;

                    if (data['success'] === true) {
                        toaster.pop('success', 'Done', 'New Problem added successfully');
                        $scope.problems.push(data['common_problem']);
                        $scope.unset_new_problem(new_problem);

                    } else if (data['success'] === false) {
                        toaster.pop('error', 'Error', data['msg']);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong');
                    }


                });


            };

            $scope.add_new_problem = function (problem_term, concept_id, new_problem, type) {
                if (problem_term === '' || problem_term === undefined || concept_id === '' || concept_id === undefined) {
                    return false;
                }

                var c = confirm("Are you sure?");

                if (c === false) {
                    return false;
                }


                var form = {};
                form.staff_id = $scope.active_user.user.id;
                form.problem_name = problem_term;
                form.concept_id = concept_id;
                form.problem_type = type;

                staffService.addCommonProblem(form).then(function (response) {
                    let data = response.data;
                    if (data['success'] === true) {
                        toaster.pop('success', 'Done', 'New Problem added successfully');
                        $scope.problems.push(data['common_problem']);
                        $scope.unset_new_problem(new_problem);
                    } else if (data['success'] === false) {
                        toaster.pop('error', 'Error', data['msg']);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong');
                    }
                });
            };

            $scope.remove_common_problem = function (problem) {
                staffService.removeCommonProblem(problem.id).then(function (response) {
                    let data = response.data;
                    if (data['success'] === true) {
                        toaster.pop('success', 'Done', 'Removed Problem successfully');
                        $scope.problems.splice($scope.problems.indexOf(problem), 1);
                    } else if (data['success'] === false) {
                        toaster.pop('error', 'Error', data['msg']);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong');
                    }
                });
            }


        }); /* End of controller */
})();