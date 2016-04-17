(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('HomeCtrl', function( $scope, $routeParams, patientService, problemService, ngDialog, toaster, $location, todoService){

			

			patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];

			});

			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var user_id = $('#user_id').val();
            $scope.user_id = user_id;
			$scope.show_accomplished_todos = false;
			$scope.problem_terms = [];
			$scope.new_problem = {set:false};

			todoService.fetchTodoMembers($scope.patient_id).then(function(data){
                $scope.members = data['members'];
            });

            todoService.fetchLabels($scope.patient_id).then(function(data){
                $scope.labels = data['labels'];
            });

	  		function convertDateTime(problem){
				if(problem.start_date) {
					var dateTime = problem.start_date;
					var date = dateTime.split("-");
				    var yyyy = date[0];
				    var mm = date[1];
				    var dd = date[2];

				    if (problem.start_time) {
				    	return dd + '/' + mm + '/' + yyyy + ' ' + problem.start_time;
				    }

				    return dd + '/' + mm + '/' + yyyy + ' 00:00:00';
				}
			    return '30/11/1970 00:00:00';
			}

			function convertDateTimeBirthday(dateTime){
				if(dateTime) {
					var date = dateTime.split("-");
				    var yyyy = date[0];
				    var mm = date[1];
				    var dd = date[2];

				    return dd + '/' + mm + '/' + yyyy + ' 00:00:00';
				}
			    return '30/11/1970 00:00:00';
			}

			function getTimelineWidgetState(problem) {
				if (problem.is_active) {
					if (problem.is_controlled) {
						return 'controlled';
					}
					return 'uncontrolled';
				}
				return 'inactive';
			}

			function parseTimelineWithoutSegment(problem) {
                var state = getTimelineWidgetState(problem);

				var timeline_problem = {
					'name': problem.problem_name,
					'id': problem.id,
					events: [
						{ 
							event_id: new Date().getTime(), 
							startTime: convertDateTime(problem), 
							state: state 
						},
					]
				};

				return timeline_problem;
			}

			function parseTimelineWithSegment(problem) {
				var events = [];
				var event;
				
				angular.forEach(problem.problem_segment, function(value) {
					event = {};
					event['event_id'] = value.event_id;
					event['startTime'] = convertDateTime(value);
					event['state'] = getTimelineWidgetState(value);
					events.push(event);
				});

				events.push({event_id: new Date().getTime(), startTime: convertDateTime(problem), state: getTimelineWidgetState(problem)});

				var timeline_problem = {
					'name': problem.problem_name,
					'id': problem.id,
					events: events
				};

				return timeline_problem;
			}

			$scope.timelineSave = function (newData) { 
				var form = {};

				form.patient_id = $scope.patient_id;
				form.timeline_data = newData;

				problemService.updateByPTW(form).then(function(data){

					toaster.pop('success', 'Done', 'Updated Problems');
				});
			};

			patientService.fetchPatientInfo(patient_id).then(function(data){
				$scope.patient_info = data['info'];
				$scope.problems = data['problems'];
				$scope.inactive_problems = data['inactive_problems'];
				$scope.goals = data['goals'];
				$scope.completed_goals = data['completed_goals'];
				$scope.pending_todos = data['pending_todos'];
				$scope.accomplished_todos = data['accomplished_todos'];
				$scope.problem_todos = data['problem_todos'];
				$scope.encounters = data['encounters'];

				// problem timeline
				var timeline_problems = [];
				angular.forEach(data['timeline_problems'], function(value, key) {

                    if (value.problem_segment) {
                    	var timeline_problem = parseTimelineWithSegment(value);
                    } else {
                    	var timeline_problem = parseTimelineWithoutSegment(value);
                    }
				  	timeline_problems.push(timeline_problem);
				});

				$scope.timeline = {
					Name: data['info']['user']['first_name'] + data['info']['user']['last_name'], 
					birthday: convertDateTimeBirthday(data['info']['date_of_birth']), 
					problems: timeline_problems
				};

				$scope.timeline_changed = true;

				$scope.todos_ready = true;
			});


			patientService.fetchPainAvatars(patient_id).then(function(data){
				$scope.pain_avatars = data['pain_avatars'];
			});

			$scope.update_patient_summary = function(){

					var form = {
						'patient_id': $scope.patient_id,
						'summary' : $scope.patient_info.summary
					};

					patientService.updatePatientSummary(form).then(function(data){
						toaster.pop('success', 'Done', 'Patient summary updated!');
					});

			};


			$scope.toggle_accomplished_todos  = function(){

				var flag = $scope.show_accomplished_todos;

				if(flag==true){
					flag = false;
				}else{
					flag=true;
				}

				$scope.show_accomplished_todos = flag;
			}







			$scope.add_goal = function(form){

				form.patient_id = $scope.patient_id;
				patientService.addGoal(form).then(function(data){

					
					var new_goal = data['goal'];

					$scope.goals.push(new_goal);

					toaster.pop('success', "Done", "New goal created successfully!");
					console.log('pop');
					
				});
				
			}


			$scope.add_todo = function(form){

				form.patient_id = $scope.patient_id;

				patientService.addToDo(form).then(function(data){

					
					var new_todo = data['todo'];
					$scope.pending_todos.push(new_todo);
					$scope.problem_todos.push(new_todo);

					$scope.new_todo = {};

					toaster.pop('success', 'Done', 'New Todo added successfully');

					/* Not-angular-way */
					$('#todoNameInput').focus();
				});

			};




			$scope.$watch('problem_term', function(newVal, oldVal){

				console.log(newVal);
				if (newVal==undefined){
					return false;
				}

				$scope.unset_new_problem();

				if(newVal.length>2){

					patientService.listTerms(newVal).then(function(data){

						$scope.problem_terms = data;

					});
				}else{

					$scope.problem_terms = [];

				}

			});



			

			$scope.set_new_problem = function(problem){

					$scope.new_problem.set = true;
					$scope.new_problem.active = problem.active;
					$scope.new_problem.term = problem.term;
					$scope.new_problem.code = problem.code;


			};


			$scope.unset_new_problem = function(){

				$scope.new_problem.set = false;

			};


			$scope.add_problem = function(){

				var c = confirm("Are you sure?");

				if(c==false){
					return false;
				}

				var form = {};
				form.patient_id = $scope.patient_id;
				form.term = $scope.new_problem.term;
				form.code = $scope.new_problem.code;
				form.active = $scope.new_problem.active;

				patientService.addProblem(form).then(function(data){

					if(data['success']==true){
						toaster.pop('success', 'Done', 'New Problem added successfully');
						$scope.problems.push(data['problem']);
						$scope.problem_term = '';
						$scope.unset_new_problem();
						/* Not-angular-way */
						$('#problemTermInput').focus();

					}else if(data['success']==false){
						alert(data['msg']);
					}else{
						alert("Something went wrong");
					}


				});


			}

			$scope.add_new_problem = function(problem_term) {
				if(problem_term == '' || problem_term == undefined) {
					return false;
				}
				
				var c = confirm("Are you sure?");

				if(c==false){
					return false;
				}


				var form = {};
				form.patient_id = $scope.patient_id;
				form.term = problem_term;

				patientService.addProblem(form).then(function(data){

					if(data['success']==true){
						toaster.pop('success', 'Done', 'New Problem added successfully');
						$scope.problems.push(data['problem']);
						$scope.problem_term = '';
						$scope.unset_new_problem();
						/* Not-angular-way */
						$('#problemTermInput').focus();
					}else if(data['success']==false){
						toaster.pop('error', 'Error', data['msg']);
					}else{
						toaster.pop('error', 'Error', 'Something went wrong');
					}
				});
			}

			$scope.update_todo_status = function(todo){

				patientService.updateTodoStatus(todo).then(function(data){

					if(data['success']==true){
						$scope.pending_todos = data['pending_todos'];
						$scope.accomplished_todos = data['accomplished_todos'];
						toaster.pop('success', "Done", "Updated Todo status !");
					}else{
						alert("Something went wrong!");
					}
					
				});				

			}

			$scope.open_problem = function(problem){

				var form = {};
				form.problem_id = problem.id;
				problemService.trackProblemClickEvent(form).then(function(data){

					$location.path('/problem/'+problem.id);

				});
				

			};


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


		}); /* End of controller */


})();