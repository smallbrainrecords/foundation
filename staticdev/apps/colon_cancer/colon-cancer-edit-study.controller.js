(function () {

    'use strict';

    angular.module('ManagerApp')
        .controller('EditStudyCtrl', function ($scope, $routeParams, ngDialog, toaster, $location, colonService, sharedService, patientService, Upload) {


            $scope.colon_id = $routeParams.colon_id;
            $scope.study_id = $routeParams.study_id;
            $scope.study = {};
            $scope.findings = [
                'fecal occult blood test',
                'colonoscopy',
                'fecal immunochemical test',
                'other'
            ];
            $scope.results = [];

            $scope.update_results = update_results;
            $scope.saveStudy = saveStudy;
            $scope.open_image_upload_box = open_image_upload_box;
            $scope.open_image_box = open_image_box;
            $scope.delete_study_image = delete_study_image;
            $scope.checkPermitted = checkPermitted;

            init();

            function init() {

                colonService.fetchColonCancerInfo($scope.colon_id).then(function (data) {
                    $scope.colon_cancer = data['info'];
                });

                colonService.fetchColonCancerStudyInfo($scope.study_id).then(function (data) {
                    $scope.study = data['info'];
                    $scope.study.study_date = moment($scope.study.study_date, "YYYY-MM-DD").format("MM/DD/YYYY");
                    $scope.update_results($scope.study.finding);
                });
            }

            function update_results(finding) {
                if (finding == 'fecal occult blood test') {
                    $scope.results = [
                        'all negative',
                        'one positive',
                        'two positive',
                        'all positive',
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
                        'negative'
                    ];
                } else if (finding == 'other') {
                    $scope.results = [
                        'positive',
                        'negative'
                    ];
                }
            }

            function saveStudy(study) {
                if (study.finding == '' || study.result == '' || study.study_date == '') {
                    toaster.pop('error', 'Error', 'Please select!');
                } else {
                    colonService.saveStudy(study).then(function (data) {
                        if (study.finding == 'colonoscopy' && study.result == 'adenomatous polyps') {
                            var factor = {value: 'personal history of adenomatous polyp', checked: true};
                            colonService.addFactor($scope.colon_id, factor).then(function (data) {
                                toaster.pop('success', 'Done', 'Saved study!');
                            });
                        } else {
                            toaster.pop('success', 'Done', 'Saved study!');
                        }
                    });
                }
            }

            function open_image_upload_box(files) {
                var url = `/colon_cancer/study/${$scope.study_id}/upload_image`;
                // var url = '/p/problem/' + $scope.problem_id + '/upload_image';
                $scope.files = files;
                if (files && files.length) {
                    Upload.upload({
                        url: url,
                        data: {
                            files: files
                        },
                        headers: {'Content-Type': undefined}
                    }).then(uploadSuccess);
                }

                function uploadSuccess(response) {
                    toaster.pop('success', 'Done', 'Image uploaded');

                    $scope.study.study_images = $scope.study.study_images.concat(response.data.images);
                }


            }

            function open_image_box(image) {

                ngDialog.open({
                    template: 'imageBoxDialog',
                    className: 'ngdialog-theme-default large-modal',
                    scope: $scope,
                    cache: false,
                    controller: ['$scope',
                        function ($scope) {

                            $scope.image = image;

                        }]
                });

            }

            function delete_study_image(image) {

                var c = confirm("Are you sure ?");

                if (c == false) {
                    return false;
                }

                var form = {};
                form.study_id = $scope.study_id;
                form.image_id = image.id;

                colonService.deleteStudyImage(form).then(function (data) {

                    var image_index = $scope.study.study_images.indexOf(image);

                    $scope.study.study_images.splice(image_index, 1);
                    toaster.pop('success', 'Done', 'Deleted image!');
                });
            }

            function checkPermitted(study, active_user) {
                if (active_user) {
                    if (active_user.role == 'physician' || active_user.role == 'admin' || active_user.id == study.author.id) {
                        return true;
                    } else {
                        return false;
                    }
                }
                return false;
            }
        })

})();