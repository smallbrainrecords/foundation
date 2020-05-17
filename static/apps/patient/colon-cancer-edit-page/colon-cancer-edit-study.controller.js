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
        .controller('EditStudyCtrl', function ($scope, $routeParams, ngDialog, toaster, colonService, Upload, DATE_CONFIG, COLON_FINDING) {
            $scope.study = {};

            $scope.dateConfig = DATE_CONFIG;
            $scope.isOpened = false;
            $scope.findingSet = COLON_FINDING;
            $scope.colonCancerStudyFormModel = {
                finding: "",
                result: "",
                date: new Date(),
                note: "",
            };

            $scope.checkPermitted = checkPermitted;
            $scope.saveStudy = saveStudy;

            init();

            function checkPermitted(study, active_user) {
                return ['admin', 'physician'].includes(active_user.role) || study.author.id === active_user.id;
            }

            function init() {
                // TODO: To be improved
                colonService.fetchColonCancerInfo($routeParams.colonId).then(function (data) {
                    $scope.colon_cancer = data['info'];
                });

                colonService.fetchColonCancerStudyInfo($routeParams.studyId)
                    .then((data) => {
                        $scope.study = data['info'];
                        $scope.colonCancerStudyFormModel.finding = $scope.findingSet.find(finding => finding.label === $scope.study.finding);
                        $scope.colonCancerStudyFormModel.result = $scope.study.result;
                        $scope.colonCancerStudyFormModel.date = moment($scope.study.study_date).toDate();
                        $scope.colonCancerStudyFormModel.note = $scope.study.note;
                    });
            }

            function saveStudy() {
                let colonCancerStudyDataModel = {
                    finding: $scope.colonCancerStudyFormModel.finding.label,
                    result: $scope.colonCancerStudyFormModel.result,
                    date: $scope.colonCancerStudyFormModel.date.toISOString(),
                    note: $scope.colonCancerStudyFormModel.note,
                };

                colonService.updateStudy($routeParams.colonId, $routeParams.studyId, colonCancerStudyDataModel)
                    .then((data) => {
                        if (data.success)
                            toaster.pop('success', 'Done', 'Saved study!');
                    });
            }
        })
})();