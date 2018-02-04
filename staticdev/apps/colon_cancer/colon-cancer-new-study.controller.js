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
        .controller('AddNewStudyCtrl', AddNewStudyCtrl);

    AddNewStudyCtrl.$inject = ['$scope', '$routeParams', 'ngDialog', 'toaster', '$location', 'sharedService', 'colonService', 'Upload'];

    function AddNewStudyCtrl($scope, $routeParams, ngDialog, toaster, $location, sharedService, colonService, Upload) {

        $scope.colon_id = $routeParams.colon_id;
        $scope.study = {};
        $scope.findings = [
            'fecal occult blood test',
            'colonoscopy',
            'fecal immunochemical test',
            'other'
        ];
        $scope.results = [];
        $scope.update_results = update_results;
        $scope.addStudy = addStudy;

        init();

        function init() {

            colonService.fetchColonCancerInfo($scope.colon_id).then(function (data) {
                $scope.colon_cancer = data['info'];
            });
        }

        function update_results(finding) {
            if (finding == 'fecal occult blood test') {
                $scope.results = [
                    'all negative',
                    'one positive',
                    'two positive',
                    'all positive'
                ];
            } else if (finding == 'colonoscopy') {
                $scope.results = [
                    'no polyps',
                    'hyperplastic polyps < 10 mm',
                    'adenomatous polyps',
                    'serrated polyps',
                    'cancer',
                ];
            } else if (finding == 'fecal immunochemical test') {
                $scope.results = [
                    'positive',
                    'negative',
                ];
            } else if (finding == 'other') {
                $scope.results = [
                    'positive',
                    'negative',
                ];
            }
        };

        function addStudy(study, image) {
            if (study.finding == '' || study.result == '' || study.date == '' || study.finding == undefined || study.result == undefined || study.date == undefined) {
                toaster.pop('error', 'Error', 'Please select!');
            } else {
                colonService.addNewStudy($scope.colon_id, study).then(function (data) {
                    let form = {};
                    form.study_id = data.study.id;

                    if (study.finding === 'colonoscopy' && study.result === 'adenomatous polyps') {
                        var factor = {value: 'personal history of adenomatous polyp', checked: true};
                        colonService.addFactor($scope.colon_id, factor).then(function (data) {
                            if (image) {
                                colonService.addImage(form, image).then(function (data) {
                                    if (data['success']) {
                                        toaster.pop('success', 'Done', 'Added study!');
                                    } else if (!data['success']) {
                                        toaster.pop('error', 'Error', 'Please fill valid data');
                                    } else {
                                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                                    }
                                    $location.url('/problem/' + $scope.colon_cancer.problem.id);
                                });
                            } else {
                                $location.url('/problem/' + $scope.colon_cancer.problem.id);
                            }
                        });
                    } else {
                        if (image) {
                            colonService.addImage(form, image).then(function (data) {
                                if (data['success']) {
                                    toaster.pop('success', 'Done', 'Added study!');
                                } else if (!data['success']) {
                                    toaster.pop('error', 'Error', 'Please fill valid data');
                                } else {
                                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                                }
                                $location.url('/problem/' + $scope.colon_cancer.problem.id);
                            });
                        } else {
                            $location.url('/problem/' + $scope.colon_cancer.problem.id);
                        }
                    }

                    study.finding == '';
                    study.result == '';
                    study.date == '';
                });
            }
        }
    }
})();