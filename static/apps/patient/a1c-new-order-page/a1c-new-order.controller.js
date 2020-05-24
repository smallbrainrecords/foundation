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
    angular.module('ManagerApp')
        .controller('AddDifferentOrderCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                       sharedService, toaster, $location, patientService) {
            $scope.a1c_id = $routeParams.a1c_id;
            $scope.add_todo = add_todo;

            init();

            function init() {

                a1cService.fetchA1cInfo($scope.a1c_id).then(function (response) {
                    let data = response.data;
                    $scope.a1c = data['info'];
                });
            }


            function add_todo(form) {
                if (form === undefined) {
                    return false;
                }

                if (form.month !== '' && form.month !== undefined) {
                    form.due_date = moment().add(form.month, "months").format("MM/DD/YYYY");
                    form.name = 'a1c repeats in ' + form.month + ' months';
                }

                if (form.name.trim().length < 1) {
                    return false;
                }

                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.a1c.problem.id;
                form.a1c_id = $scope.a1c.id;

                if ($scope.bleeding_risk) {
                    let bleedingRiskDialog = ngDialog.open({
                        template: 'bleedingRiskDialog',
                        showClose: false,
                        closeByEscape: false,
                        closeByDocument: false,
                        closeByNavigation: false
                    });

                    bleedingRiskDialog.closePromise.then(() => {
                        patientService.addProblemTodo(form).then(addTodoSuccess);
                    });
                } else {
                    patientService.addProblemTodo(form).then(addTodoSuccess);
                }

                // Add todo succeeded
                function addTodoSuccess(data) {
                    form.name = '';
                    form.month = '';
                    toaster.pop('success', 'Done', 'Added Todo!');
                    $location.url('/problem/' + $scope.a1c.problem.id);
                }
            }
        })
})();