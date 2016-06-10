(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('HomeCtrl', function( $scope, $routeParams, patientService, problemService, encounterService, ngDialog, toaster, $location, todoService, prompt, $timeout){

			

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
			$scope.new_list = {};
			$scope.new_list.labels = [];
			$scope.problem_lists = [];
			$scope.is_home = true;

			todoService.fetchTodoMembers($scope.patient_id).then(function(data){
                $scope.members = data['members'];
            });

            todoService.fetchLabels($scope.patient_id).then(function(data){
                $scope.labels = data['labels'];
            });

            problemService.fetchLabels($scope.patient_id, $scope.user_id).then(function(data){
                $scope.problem_labels = data['labels'];
            });

            problemService.fetchLabeledProblemList($scope.patient_id, $scope.user_id).then(function(data){
                $scope.problem_lists = data['problem_lists'];
                $scope.problems_ready = true;
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
				$scope.favorites = data['favorites'];
				$scope.most_recent_encounter_summarries = data['most_recent_encounter_summarries'];
				$scope.most_recent_encounter_related_problems = data['most_recent_encounter_related_problems'];
				$scope.shared_patients = data['shared_patients'];
				$scope.sharing_patients = data['sharing_patients'];

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

				var tmpListProblem = $scope.problems;

                $scope.sortingLogProblem = [];
                $scope.sortedProblem = false;
                $scope.draggedProblem = false;
				$scope.sortableOptionsProblem = {
                    update: function(e, ui) {
                        $scope.sortedProblem = true;
                    },
                    start: function() {
                        $scope.draggedProblem = true;
                    },
                    stop: function(e, ui) {
                        // this callback has the changed model
                        if ($scope.sortedProblem) {
                            $scope.sortingLogProblem = [];
                            tmpListProblem.map(function(i){
                                $scope.sortingLogProblem.push(i.id);
                            });
                            var form = {};

                            form.problems = $scope.sortingLogProblem;
                            form.patient_id = $scope.patient_id;

                            patientService.updateProblemOrder(form).then(function(data){
                                toaster.pop('success', 'Done', 'Updated Problem Order');
                            });
                        }
                        $scope.sortedProblem = false;
                        $timeout(function() {
                            $scope.draggedProblem = false;
                        }, 100);
                    }
                }
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
				
				if (!$scope.draggedProblem) {
                   	$location.path('/problem/'+problem.id);
                }
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


			// label problem list
			$scope.add_new_list_label = function(new_list, label) {
				var index = new_list.labels.indexOf(label);
				if (index > -1)
					new_list.labels.splice(index, 1);
				else
					new_list.labels.push(label);
			};

			$scope.add_problem_list = function(form){

				form.user_id = $scope.user_id;
				form.patient_id = $scope.patient_id;
				if (form.name && form.labels.length > 0)
				{
					problemService.addProblemList(form).then(function(data){
						var new_list = data['new_list'];
						$scope.problem_lists.push(new_list);
						$scope.new_list = {};
						$scope.new_list.labels = [];
						toaster.pop('success', 'Done', 'New Problem List added successfully');
					});
				} else {
					toaster.pop('error', 'Error', 'Please select name and labels');
				}
			};

			$scope.set_collapse = function(list) {
				if (list.rename==false)
					list.collapse = !list.collapse;
			};

			$scope.delete_list = function(list) {
				prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a problem list is forever. There is no undo."
                }).then(function(result){
                    problemService.deleteProblemList(list).then(function(data){
						var index = $scope.problem_lists.indexOf(list);
						$scope.problem_lists.splice(index, 1);
						toaster.pop('success', 'Done', 'Problem List removed successfully');
					});
                },function(){
                    return false;
                });
			};

			$scope.rename_list = function(list) {
				if(list.name) {
					problemService.renameProblemList(list).then(function(data){
						list.rename = false;
						toaster.pop('success', 'Done', 'Problem List renamed successfully');
					});
				} else {
					toaster.pop('error', 'Error', 'Please input name!');
				}
                
			};

			$scope.update_patient_note = function(){

				var form = {
					'patient_id': $scope.patient_id,
					'note' : $scope.patient_info.note
				};

				patientService.updatePatientNote(form).then(function(data){
					toaster.pop('success', 'Done', 'Patient note updated!');
				});

			};

			// encounter

            $scope.unmarkFavoriteEvent = function(encounter_event){
                  var form = {};
                  form.encounter_event_id = encounter_event.id;
                  form.is_favorite = false;
                  encounterService.markFavoriteEvent(form).then(function(data){
                        $scope.favorites.splice($scope.favorites.indexOf(encounter_event), 1);
                        toaster.pop('success', 'Done', 'Unmarked favorite!');
                  });
            };

            $scope.nameFavoriteEvent = function(encounter_event){
                  var form = {};
                  form.encounter_event_id = encounter_event.id;
                  form.name_favorite = encounter_event.name_favorite;
                  encounterService.nameFavoriteEvent(form).then(function(data){
                        encounter_event.is_named = false;
                        toaster.pop('success', 'Done', 'Named favorite!');
                  });
            };

            function copyToClipboard(text) {
				var $temp = $("<textarea/>")
				$("body").append($temp);
				$temp.val(text).select();
				document.execCommand("copy");
				$temp.remove();
			}

            $(window).keydown(function(event) {
			  if(event.ctrlKey && event.keyCode == 67 && $location.path() == '/') { 
			    var text = '';

			    // encounter copy
			    if ($scope.most_recent_encounter_summarries.length > 0) {
			    	text += "All the encounter summaries from the most recent encounter: \r\n";
			    	angular.forEach($scope.most_recent_encounter_summarries, function(value, key) {
						text += value + '\r\n';
					});
					text += '\r\n';
			    }

			    if ($scope.most_recent_encounter_related_problems.length > 0) {
			    	text += "List of related problems : \r\n";
			    	angular.forEach($scope.most_recent_encounter_related_problems, function(value, key) {
						text += value.problem_name + '\r\n';
					});
					text += '\r\n';
			    }

			    if ($scope.pending_todos.length > 0) {
			    	text += "List of all active todos : \r\n";
			    	angular.forEach($scope.pending_todos, function(value, key) {
						text += value.todo + '\r\n';
					});
			    }

			    copyToClipboard(text)
			    event.preventDefault();
			  }
			});


		}); /* End of controller */


})();