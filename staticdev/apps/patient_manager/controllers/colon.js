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

            $scope.addStudy = function(study, image) {
                if (study.finding == '' || study.result == '' || study.date == '' || study.finding == undefined || study.result == undefined || study.date == undefined) {
                    toaster.pop('error', 'Error', 'Please select!');
                } else {
                    colonService.addNewStudy($scope.colon_id, study).then(function(data){
                        var form = {};
                        form.study_id = data.study.id;

                        colonService.addImage(form, image).then(function(data){
                            if(data['success']==true){
                                toaster.pop('success', 'Done', 'Added study!');
                            }else if(data['success']==false){
                                toaster.pop('error', 'Error', 'Please fill valid data');
                            }else{
                                toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                            }
                            $location.url('/problem/' + $scope.colon_cancer.problem.id);
                        });
                        
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
            };

            $scope.image_upload_url = function(){

                var url = '/colon_cancer/study/'+$scope.study_id+'/upload_image';
                return url;
            }

            $scope.open_image_upload_box = function(){
                ngDialog.open({
                    template:'/static/apps/patient_manager/partials/modals/upload_image.html',
                    className:'ngdialog-theme-default large-modal',
                    scope:$scope,
                    cache:false,
                    controller: ['$scope',
                    function($scope){
                    }]
                });
            };


            $scope.open_image_box = function(image){

                    ngDialog.open({
                        template:'/static/apps/patient_manager/partials/modals/image.html',
                        className:'ngdialog-theme-default large-modal',
                        scope:$scope,
                        cache:false,
                        controller: ['$scope',
                        function($scope){

                            $scope.image = image;

                        }]
                    });

            };

            $scope.delete_study_image = function(image){

                var c = confirm("Are you sure ?");

                if(c==false){
                    return false;
                }

                var form = {};
                form.study_id = $scope.study_id;
                form.image_id = image.id;

                colonService.deleteStudyImage(form).then(function(data){

                    var image_index = $scope.study.study_images.indexOf(image);

                    $scope.study.study_images.splice(image_index, 1);
                    toaster.pop('success', 'Done', 'Deleted image!');
                });
            };

        }); /* End of controller */


})();