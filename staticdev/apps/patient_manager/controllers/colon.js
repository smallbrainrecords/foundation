(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('AddNewStudyCtrl', function($scope, $routeParams, ngDialog, toaster, $location, colonService){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
            $scope.colon_id = $routeParams.colon_id;
			$scope.study = {};

            $scope.findings = [
                'fecal occult blood test',
                'colonoscopy',
                'fecal immunochemical test',
                'other',
            ];

            $scope.results = [];

			colonService.fetchColonCancerInfo($scope.colon_id).then(function(data){
                $scope.colon_cancer = data['info'];
            });

            $scope.update_results = function(finding) {
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
                        'negative',
                    ];
                } else if (finding == 'other') {
                    $scope.results = [
                        'positive',
                        'negative',
                    ];
                }
            }

            $scope.addStudy = function(study) {
                if (study.finding == '' || study.result == '' || study.date == '' || study.finding == undefined || study.result == undefined || study.date == undefined) {
                    toaster.pop('error', 'Error', 'Please select!');
                } else {
                    colonService.addNewStudy($scope.colon_id, study).then(function(data){
                        toaster.pop('success', 'Done', 'Added study!');
                        $location.url('/problem/' + $scope.colon_cancer.problem.id);
                    });
                }
            }

		}) /* End of controller */
        .controller('EditStudyCtrl', function($scope, $routeParams, ngDialog, toaster, $location, colonService){


            var patient_id = $('#patient_id').val();
            $scope.patient_id = patient_id;
            $scope.colon_id = $routeParams.colon_id;
            $scope.study_id = $routeParams.study_id;
            $scope.study = {};

            $scope.findings = [
                'fecal occult blood test',
                'colonoscopy',
                'fecal immunochemical test',
                'other',
            ];

            $scope.results = [];

            colonService.fetchColonCancerInfo($scope.colon_id).then(function(data){
                $scope.colon_cancer = data['info'];
            });

            colonService.fetchColonCancerStudyInfo($scope.study_id).then(function(data){
                $scope.study = data['info'];
                $scope.study.study_date = moment($scope.study.study_date, "YYYY-MM-DD").format("MM/DD/YYYY");
                $scope.update_results($scope.study.finding);
            });

            $scope.update_results = function(finding) {
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
                        'negative',
                    ];
                } else if (finding == 'other') {
                    $scope.results = [
                        'positive',
                        'negative',
                    ];
                }
            }

            $scope.saveStudy = function(study) {
                if (study.finding == '' || study.result == '' || study.study_date == '') {
                    toaster.pop('error', 'Error', 'Please select!');
                } else {
                    colonService.saveStudy(study).then(function(data){
                        toaster.pop('success', 'Done', 'Saved study!');
                    });
                }
            }

        }); /* End of controller */


})();