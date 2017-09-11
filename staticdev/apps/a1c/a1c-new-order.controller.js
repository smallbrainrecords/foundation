(function () {
    'use strict';
    angular.module('ManagerApp')
        .controller('AddDifferentOrderCtrl', function ($scope, $routeParams, a1cService, ngDialog, problemService,
                                                       sharedService, toaster, $location, patientService) {
            $scope.a1c_id = $routeParams.a1c_id;
            $scope.add_todo = add_todo;

            init();

            function init() {

                a1cService.fetchA1cInfo($scope.a1c_id).then(function (data) {
                    $scope.a1c = data['info'];
                });
            }


            function add_todo(form) {
                if (form == undefined) {
                    return false;
                }

                if (form.month != '' && form.month != undefined) {
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

                    bleedingRiskDialog.closePromise.then(function () {
                        debugger;
                        patientService.addProblemTodo(form).then(addTodoSuccess);
                    });
                } else {
                    debugger;
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