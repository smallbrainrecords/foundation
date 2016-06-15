(function(){

	'use strict';


	angular.module('StaffApp')
		.controller('ManageSharingCtrl', function(
			$scope, $routeParams, ngDialog, 
			staffService, $location, $anchorScroll, toaster){

			staffService.getPatientsList().then(function(data){
				$scope.patients_list = data['patients_list'];
			});



		}); /* End of controller */


	angular.module('StaffApp')
		.controller('ManageSharingPatientCtrl', function(
			$scope, $routeParams, ngDialog, 
			staffService, $location, $anchorScroll, toaster){

			$scope.init = function(){

				$scope.patient_id = $routeParams['patientId'];

				$scope.assign_patient_form = {};

				staffService.fetchActiveUser().then(function(data){
					$scope.active_user = data['user_profile'];
				});
				
				staffService.getUserInfo($scope.patient_id).then(function(data){
					$scope.patient = data['user_profile'];
				});

				staffService.getPatientsList().then(function(data){
					$scope.patients_list = data['patients_list'];
				});

				staffService.getSharingPatients($scope.patient_id).then(function(data){
					$scope.sharing_patients = data['sharing_patients'];
				});

			}

			$scope.add_sharing_patient = function(form) {
				form.patient_id = $scope.patient_id;

				staffService.addSharingPatient(form).then(function(data){
					if(data['success']==true){
						$scope.sharing_patients.push(data['sharing_patient']);
						form.sharing_patient_id = '';

						toaster.pop('success', 'Done', 'Added sharing patient successfully');
					} else {
						toaster.pop('error', 'Error', 'Something error! Please try again!');
					}
				});
			}

			$scope.remove_sharing_patient = function(p) {
				staffService.removeSharingPatient($scope.patient_id, p.user.id).then(function(data){
					if(data['success']==true){
						var index = $scope.sharing_patients.indexOf(p);
						$scope.sharing_patients.splice(index, 1);

						toaster.pop('success', 'Done', 'Removed sharing patient successfully');
					} else {
						toaster.pop('error', 'Error', 'Something error! Please try again!');
					}
				});
			}

			$scope.permitted = function(p){
				var permitted = true;
				if(p.user.id == $scope.patient.user.id){
					permitted = false;
				}

				angular.forEach($scope.sharing_patients, function(value, key) {
					if(p.user.id == value.user.id){
						permitted = false;
					}
				});

				return permitted;

			};
			
			$scope.init();

		}); /* End of controller */


})();