(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('DataCtrl', function($scope, $routeParams, ngDialog, problemService, toaster, $location, dataService, patientService){

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			$scope.data_id = $routeParams.data_id;

			patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];

			});

            dataService.fetchDataInfo($scope.data_id).then(function(data){
                $scope.data = data['info'];
            });

            problemService.fetchProblems($scope.patient_id).then(function(data){
                $scope.problems = data['problems'];

                dataService.fetchPinToProblem($scope.data_id).then(function(data){
	                $scope.pins = data['pins'];

	                angular.forEach($scope.problems, function(problem) {
	                	if ($scope.isInPins($scope.pins, problem)) {
	                		problem.pin = true;
	                	}
	                });
	            });
            });

            $scope.isInPins = function (array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value.problem == item.id) {
                        is_existed = true;
                    }
                });
                return is_existed;
            };

            /*
            * toggle pin to new problem, display list of current patient problems
            */
            $scope.show_pin_to_new_problem = false;
            $scope.toggle_pin_to_new_problem = function() {
            	$scope.show_pin_to_new_problem = !$scope.show_pin_to_new_problem;
            };

            $scope.data_pin_to_problem = function(data_id, problem_id) {
            	var form = {};
            	form.data_id = data_id;
            	form.problem_id = problem_id;

            	dataService.dataPinToProblem($scope.patient_id, form).then(function(data){
	                if(data['success']==true){
                        toaster.pop('success', 'Done', 'Pinned problem!');
                    }else if(data['success']==false){
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    }else{
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
	            });
            };

			
        }) /* End of controller */
        .controller('AddDataCtrl', function($scope, $routeParams, ngDialog, problemService, toaster, $location, dataService, patientService){

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			$scope.data_id = $routeParams.data_id;

			patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];

			});

            dataService.fetchDataInfo($scope.data_id).then(function(data){
                $scope.data = data['info'];
            });

            $scope.add_data = function(new_data) {
            	if (new_data.time == "" || new_data.time == undefined) {
            		new_data.time = "12:00";
            	}
            	if (!moment(new_data.time, "HH:mm").isValid()) {
            		toaster.pop('error', 'Error', 'Please enter time!');
            		return;
            	}
            	new_data.datetime = new_data.date + " " + new_data.time;
            	dataService.addData($scope.patient_id, $scope.data_id, new_data).then(function(data){
	                if(data['success']==true){
                        toaster.pop('success', 'Done', 'Added data!');
                        $location.url('/data/' + $scope.data_id);
                    }else if(data['success']==false){
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    }else{
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
	            });
            };

			
        }) /* End of controller */
        .controller('ShowAllDataCtrl', function($scope, $routeParams, ngDialog, problemService, toaster, $location, dataService, patientService){

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			$scope.data_id = $routeParams.data_id;

			patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];

			});

            dataService.fetchDataInfo($scope.data_id).then(function(data){
                $scope.data = data['info'];
            });
			
        }) /* End of controller */
        .controller('IndividualDataCtrl', function($scope, $routeParams, ngDialog, problemService, toaster, $location, dataService, patientService){

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			$scope.individual_data_id = $routeParams.individual_data_id;

			patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];

			});

            dataService.fetchIndividualDataInfo($scope.patient_id, $scope.individual_data_id).then(function(data){
                if (data['success'] == true) {
                    $scope.individual_data = data['info'];
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                }
            });
			
        }); /* End of controller */
})();