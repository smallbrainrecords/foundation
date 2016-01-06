(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('ProblemsCtrl', function($scope, $routeParams, $interval,  patientService, problemService, ngDialog, toaster){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var problem_id = $routeParams.problem_id;

			$scope.problem_id = problem_id;
			$scope.show_accomplished_todos = false;
			$scope.show_accomplished_goals = false;

			$scope.loading = true;
			$scope.show_other_notes = false;
			$scope.history_note_form = {};
			$scope.wiki_note_form = {};

			patientService.fetchActiveUser().then(function(data){

				$scope.active_user = data['user_profile'];

			});

			

			function convertDateTime(dateTime){
				if(dateTime) {
					var date = dateTime.split("-");
				    var yyyy = date[0];
				    var mm = date[1];
				    var dd = date[2];

				    return dd + '/' + mm + '/' + yyyy + ' 12:00:00';
				}
			    return '30/11/1970 12:00:00';
			}

			function convertDateTimeBack(dateTime){
				if(dateTime) {
					var date = dateTime.split("/");
				    var yyyy = date[2].split(" ")[0];
				    var mm = date[1];
				    var dd = date[0];

				    return yyyy + '-' + mm + '-' + dd;
				}
			    return '1970-11-30';
			} 

			$scope.timelineSave = function (newData) { 
				var form = {};

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				form.start_date = convertDateTimeBack(newData.problems[0].events[0].startTime);
				$scope.problem.start_date = form.start_date;

				problemService.updateStartDate(form).then(function(data){

					toaster.pop('success', 'Done', 'Updated Start Date');
					$scope.set_authentication_false();
				});
			};

			patientService.fetchProblemInfo(problem_id).then(function(data){

                    $scope.problem = data['info'];

                    // problem timeline
                    var state;
				  	if ($scope.problem.is_controlled) {
				  		state = 'controlled';
				  	} else if ($scope.problem.is_active) {
				  		state = 'uncontrolled';
				  	} else {
				  		state = 'inactive';
				  	}
					var timeline_problems = [
						{
							'name': $scope.problem.problem_name,
							events: [
			                    { event_id: null, startTime: convertDateTime($scope.problem.start_date), state: state },
							]
						}
					];

					$scope.$watch('active_user', function(nV, oV){
						$scope.timeline = {
							Name: $scope.active_user['user']['first_name'] + $scope.active_user['user']['last_name'], 
							birthday: convertDateTime($scope.active_user['date_of_birth']), 
							problems: timeline_problems
						};
					});

                    $scope.patient_notes = data['patient_notes'];
                    $scope.physician_notes = data['physician_notes'];

                    $scope.problem_goals = data['problem_goals'];
                    $scope.problem_todos = data['problem_todos'];

                    $scope.problem_images = data['problem_images'];

                    $scope.effecting_problems = data['effecting_problems'];
                    $scope.effected_problems = data['effected_problems'];

                    $scope.history_note = data['history_note'];
                    
                    var wiki_notes = data['wiki_notes'];

                    $scope.patient_wiki_notes = wiki_notes['patient'];
                    $scope.physician_wiki_notes = wiki_notes['physician'];
                    $scope.other_wiki_notes = wiki_notes['other'];
                    $scope.related_encounters = data['related_encounters'];

                    $scope.activities = data['activities'];

                    if($scope.history_note!=null){

                    	$scope.history_note_form = {
                    		note: $scope.history_note.note
                    	};

                    }
                    


                    var patient_problems = data['patient_problems'];

                    


                    for(var index in patient_problems){

                    	var id = patient_problems[index].id;

                    	if ($scope.id_exists(id, $scope.effecting_problems)==true){
                    		patient_problems[index].effecting=true
                    	}

                    	if ($scope.id_exists(id, $scope.effected_problems)==true){
                    		patient_problems[index].effected=true
                    	}


                    }

                    $scope.patient_problems = patient_problems;

                    $scope.loading = false;
            });



			/* Track Status */

			$scope.$watch('[problem.is_controlled,problem.authenticated, problem.is_active]', function(nV, oV){

				if($scope.loading==true){
					return false;
				}

				if(angular.equals(oV, [undefined, undefined, undefined])==true){
					return false;
				}

				

				var form = {};

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				form.is_controlled = $scope.problem.is_controlled;
				form.authenticated = $scope.problem.authenticated;
				form.is_active = $scope.problem.is_active;


				problemService.updateProblemStatus(form).then(function(data){

					toaster.pop('success', 'Done', 'Updated Problem Status');

				});

			});

			$scope.set_authentication_false = function() {
				if($scope.active_user.role != "physician" && $scope.active_user.role != "admin")
					$scope.problem.authenticated = false;
			}
			

			$scope.update_start_date = function(){

				var form = {};

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				form.start_date = $scope.problem.start_date;

				problemService.updateStartDate(form).then(function(data){

					toaster.pop('success', 'Done', 'Updated Start Date');
					$scope.set_authentication_false();
				});
			}

			$scope.add_wiki_note = function(form){
				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;

				problemService.addWikiNote(form).then(function(data){

					if(data['success']==true){

						toaster.pop('success', 'Done', 'Added Wiki Note');
						var note = data['note'];
						if($scope.active_user.role=='patient'){
							$scope.patient_wiki_notes.unshift(note);
						}else if($scope.active_user.role=='physician'){
							$scope.physician_wiki_notes.unshift(note);
						}else{
							$scope.show_other_notes = true;
							$scope.other_wiki_notes.unshift(note);
						}

						form.note = '';
						$scope.set_authentication_false();
					}else if(data['success']==false){
						toaster.pop('error', 'Warning', 'Action Failed');
					}else{
						toaster.pop('error', 'Warning', 'Something went wrong!');
					}


				});

			};


			$scope.add_history_note = function(form){
				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;

				problemService.addHistoryNote(form).then(function(data){

					if(data['success']==true){
						toaster.pop('success', 'Done', 'Added History Note');

						$scope.history_note = data['note'];
						$scope.set_authentication_false();
						
					}else if(data['success']==false){
						toaster.pop('error', 'Warning', 'Action Failed');
					}else{
						toaster.pop('error', 'Warning', 'Something went wrong!');
					}

				});

			};


			$scope.add_goal = function(form){

				if(form==undefined){
					return false;
				}

				if(form.name.trim().length<1){
					return false;
				}

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				problemService.addGoal(form).then(function(data){

					form.name = '';
					$scope.problem_goals.push(data['goal']);
					toaster.pop('success', 'Done', 'Added Goal!');
					$scope.set_authentication_false();
					/* Not-angular-way */
					$('#goalNameInput').focus();
				});
			}

			$scope.add_todo = function(form){


				if(form==undefined){
					return false;
				}

				if(form.name.trim().length<1){
					return false;
				}

				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				problemService.addTodo(form).then(function(data){

					form.name = '';
					$scope.problem_todos.push(data['todo']);
					toaster.pop('success', 'Done', 'Added Todo!');
					$scope.set_authentication_false();
					/* Not-angular-way */
					$('#todoNameInput').focus();
				});
			}



			$scope.image_upload_url = function(){

				var patient_id = $scope.patient_id;
				var problem_id = $scope.problem_id;
				var url = '/p/problem/'+problem_id+'/upload_image';
				return url;
			}


			$scope.open_image_box = function(image){

				    ngDialog.open({
                        template:'/static/apps/patient_manager/partials/modals/image.html',
                        className:'ngdialog-theme-default large-modal',
                        scope:$scope,
                        cache:false,
                        controller: ['$scope',
                        function($scope){

                        	$scope.image = image;

                        	$scope.set_authentication_false();
                        }]
                    });

			};

			$scope.delete_problem_image = function(image){

				var c = confirm("Are you sure ?");

				if(c==false){
					return false;
				}

				var form = {};
				form.patient_id = $scope.patient_id;
				form.problem_id = $scope.problem.id;
				form.image_id = image.id;

				problemService.deleteProblemImage(form).then(function(data){

					var image_index = $scope.problem_images.indexOf(image);

					$scope.problem_images.splice(image_index, 1);
					toaster.pop('success', 'Done', 'Added Todo!');
					$scope.set_authentication_false();
				});
			};




			$scope.update_todo_status = function(todo){

				patientService.updateTodoStatus(todo).then(function(data){

					if(data['success']==true){

						toaster.pop('success', "Done", "Updated Todo status !");
						$scope.set_authentication_false();
					}else{
						alert("Something went wrong!");
					}
					
				});				

			}


			$scope.id_exists = function(id, item_list){

				var found = false;

				angular.forEach(item_list, function(value){
					
					if(value==id){
						found = true;
					}

				});

				return found;

			}


			$scope.change_effecting_problem = function(source, problem){

				var effecting = source.effecting;

				var form = {};
				form.source_id = source.id;
				form.target_id = problem.id;
				form.relationship = effecting;
				problemService.relateProblem(form).then(function(data){
					toaster.pop('success', "Done", "Updated relationship !");
					$scope.set_authentication_false();
				});

			}

			$scope.change_effected_problem = function(problem, target){

				
				var effected = target.effected;

				var form = {};
				form.source_id = problem.id;
				form.target_id = target.id;
				form.relationship = effected;

				problemService.relateProblem(form).then(function(data){
					toaster.pop('success', "Done", "Updated relationship !");
					$scope.set_authentication_false();

				});

			}


			$scope.permitted = function(permissions){

				if($scope.active_user==undefined){
					return false;
				}

				var user_permissions = $scope.active_user.permissions;

				for(var key in permissions){

					if(user_permissions.indexOf(permissions[key])<0){
						return false;
					}
				}

				return true;

			};


			$scope.toggle_other_notes = function(){

				if($scope.show_other_notes==true){
					$scope.show_other_notes = false;
				}else{
					$scope.show_other_notes = true;
				}
			};


			$scope.refresh_problem_activity=function(){
				problemService.getProblemActivity($scope.problem_id).then(function(data){
					if ($scope.activities.length != data['activities'].length)
						$scope.activities = data['activities'];
				})
			}

			$scope.toggle_accomplished_todos  = function(){

				var flag = $scope.show_accomplished_todos;

				if(flag==true){
					flag = false;
				}else{
					flag=true;
				}

				$scope.show_accomplished_todos = flag;
			}

			$scope.toggle_accomplished_goals  = function(){

				var flag = $scope.show_accomplished_goals;

				if(flag==true){
					flag = false;
				}else{
					flag=true;
				}

				$scope.show_accomplished_goals = flag;
			}

			$interval(function(){
				$scope.refresh_problem_activity();
			}, 4000);
		}); /* End of controller */


})();