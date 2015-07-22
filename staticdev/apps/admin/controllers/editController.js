(function(){

	'use strict';


	angular.module('AdminApp')
		.controller('EditCtrl', function(
			$scope, $routeParams, ngDialog, 
			adminService, $location, $anchorScroll, toaster){




			$scope.user_id = $routeParams['userId'];

			adminService.getUserInfo($scope.user_id).then(function(data){

				$scope.user_profile = data['user_profile'];

			});

			$scope.files = {};
			$scope.password_form = {};

			$scope.update_basic_profile = function(){

				var form = {};

				form.user_id = $scope.user_id;
				form.first_name = $scope.user_profile.user.first_name;
				form.last_name = $scope.user_profile.user.last_name;

				adminService.updateBasicProfile(form).then(function(data){

					if(data['success']==true){
						/* Fix: toaster not working */

						alert("Updated");

					}else if(data['success']==false){

						alert("Please fill valid data");
					}else{
						alert("Something went wrong, we are fixing it asap!");
					}

				});

			};

			$scope.update_profile = function(){

				var form = {};

				form.user_id = $scope.user_id;
				form.phone_number = $scope.user_profile.phone_number;
				form.sex = $scope.user_profile.sex;
				form.role = $scope.user_profile.role;
				form.summary = $scope.user_profile.summary;
				form.date_of_birth = $scope.user_profile.date_of_birth;
				
				var files = $scope.files;
				

				console.log(files);
				adminService.updateProfile(form, files).then(function(data){

					if(data['success']==true){
						/* Fix: toaster not working */
						
						alert("Updated");

					}else if(data['success']==false){

						alert("Please fill valid data");
					}else{
						alert("Something went wrong, we are fixing it asap!");
					}
					
				});

			};


			$scope.update_email = function(){

				var form = {};

				form.user_id = $scope.user_id;
				form.email = $scope.user_profile.user.email;


				/* Files */

				adminService.updateEmail(form).then(function(data){

					if(data['success']==true){
						/* Fix: toaster not working */
						
						alert("Updated");

					}else if(data['success']==false){

						alert("Please fill valid data");
					}else{
						alert("Something went wrong, we are fixing it asap!");
					}
					
				});

			};


			$scope.update_password = function(){

				var form = {};

				form.user_id = $scope.user_id;
				form.new_password = $scope.password_form.new_password;
				form.verify_password = $scope.password_form.verify_password;

				/* Files */

				adminService.updatePassword(form).then(function(data){

					if(data['success']==true){
						/* Fix: toaster not working */
						
						alert("Updated Password");

					}else if(data['success']==false){

						alert("Please fill valid data");
					}else{
						alert("Something went wrong, we are fixing it asap!");
					}
				});

			};






			$scope.navigate = function(l){
				/* Replace by directive */
				
				$("html, body").animate({ scrollTop: $('#'+l).offset().top-100 }, 500);
			};

		}); /* End of controller */


})();