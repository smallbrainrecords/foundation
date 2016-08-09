(function(){

	'use strict';


	angular.module('ManagerApp')
		.controller('ProblemsCtrl', function($scope, $routeParams, $interval,  patientService, problemService, ngDialog, toaster, todoService, prompt, $cookies){


			var patient_id = $('#patient_id').val();
			$scope.patient_id = patient_id;
			var user_id = $('#user_id').val();
            $scope.user_id = user_id;
			var problem_id = $routeParams.problem_id;

			$scope.problem_id = problem_id;
			$scope.show_accomplished_todos = false;
			$scope.show_accomplished_goals = false;

			$scope.loading = true;
			$scope.show_other_notes = false;
            $scope.show_physician_notes = false;
			$scope.history_note_form = {};
			$scope.wiki_note_form = {};
			$scope.current_activity = 0;
			$scope.problem_terms = [];
			$scope.new_problem = {set:false};

			patientService.fetchActiveUser().then(function(data){
				$scope.active_user = data['user_profile'];

			});

			todoService.fetchTodoMembers($scope.patient_id).then(function(data){
                $scope.members = data['members'];
            });

			todoService.fetchLabels($scope.patient_id).then(function(data){
                $scope.labels = data['labels'];
            });

            problemService.fetchLabels($scope.patient_id, $scope.user_id).then(function(data){
                $scope.problem_labels = data['labels'];
            });

			problemService.trackProblemClickEvent(problem_id).then(function(data){});

			function convertDateTime(problem){
				if(problem.start_date) {
					var dateTime = problem.start_date;
                    console.log("Start Date: " + dateTime)
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

			function convertDateTimeBack(dateTime){
				if(dateTime) {
					var date = dateTime.split("/");
				    var yyyy = date[2].split(" ")[0];
				    var mm = date[1];
				    var dd = date[0];

				    return mm + '/' + dd + '/' + yyyy;
				}
			    return '11/30/1970';
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

				var timeline_problems = [
					{
						'name': problem.problem_name,
						'id': problem.id,
						events: [
							{
								event_id: new Date().getTime(),
								startTime: convertDateTime(problem),
								state: state
							},
						]
					}
				];

                console.log("Timeline Problems: " + JSON.stringify(timeline_problems));

				return timeline_problems;
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

				var timeline_problems = [
					{
						'name': problem.problem_name,
						'id': problem.id,
						events: events
					}
				];

				return timeline_problems;
			}

			function getStateChangedEvent(problem) {
				var event = {}
				event['event_id'] = new Date().getTime();
				event['startTime'] = moment().format('DD/MM/YYYY HH:mm:ss');
				event['state'] = getTimelineWidgetState(problem);

				return event;
			}

			$scope.timelineSave = function (newData) {
				var form = {};

				form.patient_id = $scope.patient_id;
				form.timeline_data = newData;
				$scope.problem.start_date = convertDateTimeBack(newData.problems[0].events[newData.problems[0].events.length - 1].startTime);

				problemService.updateByPTW(form).then(function(data){
					toaster.pop('success', 'Done', 'Updated Problem');
				});
			};

			patientService.fetchProblemInfo(problem_id).then(function(data){

                $scope.problem = data['info'];

                // problem timeline
                if ($scope.problem.problem_segment !== undefined && $scope.problem.problem_segment.length > 0) {
                	var timeline_problems = parseTimelineWithSegment($scope.problem);
                } else {
                	var timeline_problems = parseTimelineWithoutSegment($scope.problem);
                }

				$scope.$watch('active_user', function(nV, oV){
					$scope.timeline = {
						Name: $scope.active_user['user']['first_name'] + $scope.active_user['user']['last_name'],
						birthday: convertDateTimeBirthday($scope.active_user['date_of_birth']),
						problems: timeline_problems
					};

					$scope.timeline_changed = true;
				});

                $scope.patient_notes = data['patient_notes'];
                $scope.physician_notes = data['physician_notes'];

                $scope.problem_goals = data['problem_goals'];
                $scope.problem_todos = data['problem_todos'];
                $scope.todos_ready = true;

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
                if (data['activities'].length) {
                	$scope.current_activity = data['activities'][0].id;
                }
                $interval(function(){
					$scope.refresh_problem_activity();
				}, 10000);

				// observations
				$scope.observations = data['observations'];
				if ($scope.observations.length > 0) {
					problemService.fetchObservations(problem_id).then(function(data2) {
	                	$scope.observations = data2['observations'];
	                });
				}

				// colon_cancers
				$scope.colon_cancers = data['colon_cancer'];
				if ($scope.colon_cancers.length > 0) {
					problemService.fetchColonCancerss(problem_id).then(function(data2) {
	                	$scope.colon_cancers = data2['colon_cancers'];
	                });
				}

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


                $scope.sharing_patients = data['sharing_patients'];
            });

			// change problem name
			$scope.$watch('problem_term', function(newVal, oldVal){

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

			$scope.change_problem_name = function(){

				var c = confirm("Are you sure?");

				if(c==false){
					return false;
				}

				var form = {};
				form.term = $scope.new_problem.term;
				form.code = $scope.new_problem.code;
				form.problem_id = $scope.problem_id;

				problemService.changeProblemName(form).then(function(data){

					if(data['success']==true){
						toaster.pop('success', 'Done', 'Problem name changed successfully');
						$scope.problem = data['problem'];
						$scope.problem_term = '';
						$scope.unset_new_problem();
						/* Not-angular-way */
						$('#problemTermInput').focus();
						$scope.set_authentication_false();

					}else if(data['success']==false){
						alert(data['msg']);
					}else{
						alert("Something went wrong");
					}


				});


			}

			$scope.change_new_problem_name = function(problem_term) {
				if(problem_term == '' || problem_term == undefined) {
					return false;
				}

				var c = confirm("Are you sure?");

				if(c==false){
					return false;
				}


				var form = {};
				form.term = problem_term;
				form.problem_id = $scope.problem_id;

				problemService.changeProblemName(form).then(function(data){

					if(data['success']==true){
						toaster.pop('success', 'Done', 'Problem name changed successfully');
						$scope.problem = data['problem'];
						$scope.problem_term = '';
						$scope.unset_new_problem();
						/* Not-angular-way */
						$('#problemTermInput').focus();
						$scope.set_authentication_false();
					}else if(data['success']==false){
						toaster.pop('error', 'Error', data['msg']);
					}else{
						toaster.pop('error', 'Error', 'Something went wrong');
					}
				});
			}

			// change problem label
			$scope.change_problem_label = false;
			$scope.open_change_problem_label = function() {
				$scope.change_problem_label = true;
			}
			$scope.close_change_problem_label = function() {
				$scope.change_problem_label = false;
			}

			$scope.create_problem_label = false;
			$scope.open_create_problem_label = function() {
				$scope.create_problem_label = true;
			}
			$scope.close_create_problem_label = function() {
				$scope.create_problem_label = false;
			}

			$scope.problem_labels_component = [
                {name: 'green', css_class: 'todo-label-green'},
                {name: 'yellow', css_class: 'todo-label-yellow'},
                {name: 'orange', css_class: 'todo-label-orange'},
                {name: 'red', css_class: 'todo-label-red'},
                {name: 'purple', css_class: 'todo-label-purple'},
                {name: 'blue', css_class: 'todo-label-blue'},
                {name: 'sky', css_class: 'todo-label-sky'},
            ];
            $scope.problem_label_component = {};

            $scope.selectProblemLabelComponent = function(component) {
                $scope.problem_label_component.css_class = component.css_class;
            }

            $scope.saveCreateProblemLabel = function(problem) {
                if ($scope.problem_label_component.css_class != null) {
                    problemService.saveCreateLabel($scope.problem_id, $scope.problem_label_component).then(function(data){
                        if(data['success']==true){
                            if(data['new_status']==true){
                                $scope.problem_labels.push(data['new_label']);
                            }
                            if(data['status']==true){
                                problem.labels.push(data['label']);
                                toaster.pop('success', "Done", "Added Problem label!");
                            }
                        }else{
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                $scope.create_problem_label = false;
            }

            $scope.editProblemLabel = function(label) {
                label.edit_label = (label.edit_label != true) ? true : false;
            }

            $scope.selectEditProblemLabelComponent = function(label, component) {
                label.css_class = component.css_class;
            }

            $scope.saveEditProblemLabel = function(label) {
                if (label.css_class != null) {
                    problemService.saveEditLabel(label, $scope.patient_id, $scope.user_id).then(function(data){
                        if(data['success']==true){
                            label.css_class = data['label']['css_class'];
                            if(data['status']==true){
                                angular.forEach($scope.problem.labels, function(value, key) {
                                    if (value.id == label.id) {
                                        value.css_class = label.css_class;
                                    }
                                });
                                toaster.pop('success', "Done", "Changed label!");
                            }
                        }else{
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                label.edit_label = false;
            }

            $scope.changeProblemLabel = function(problem, label) {

                var is_existed = false;
                var existed_key;
                var existed_id;

                angular.forEach(problem.labels, function(value, key) {
                    if (value.name==label.name) {
                        is_existed = true;
                        existed_key = key;
                        existed_id = value.id;
                    }
                });
                if (!is_existed) {
                    problem.labels.push(label);
                    problemService.addProblemLabel(label.id, problem.id).then(function(data){
                        if(data['success']==true){
                            toaster.pop('success', "Done", "Added Problem label!");
                        }else{
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                } else {
                    problem.labels.splice(existed_key, 1);
                    problemService.removeProblemLabel(existed_id, problem.id).then(function(data){
                        if(data['success']==true){
                            toaster.pop('success', "Done", "Removed Problem label!");
                        }else{
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }

            }

            $scope.deleteEditProblemLabel = function(label) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a label is forever. There is no undo."
                }).then(function(result){
                    problemService.deleteLabel(label).then(function(data){
	                    var index = $scope.problem_labels.indexOf(label);
	                    $scope.problem_labels.splice(index, 1);

	                    var index2;
	                    angular.forEach($scope.problem.labels, function(value, key) {
                            if (value.id == label.id) {
                                index2 = key;
                            }
                        });
	                    if (index2 != undefined)
                            $scope.problem.labels.splice(index2, 1);

	                    toaster.pop('success', 'Done', 'Deleted label successfully');
	                });
                },function(){
                    return false;
                });
            }

            // labeled problems list
            $scope.create_label_problems_list = false;
            $scope.new_list = {};
            $scope.new_list.labels = [];
            $scope.open_create_label_problems_list = function() {
            	$scope.create_label_problems_list = true;
            };

            $scope.close_create_label_problems_list = function() {
            	$scope.create_label_problems_list = false;
            };

            $scope.add_new_list_label = function (new_list, label) {
                var index = new_list.labels.indexOf(label);
                if (index > -1)
                    new_list.labels.splice(index, 1);
                else
                    new_list.labels.push(label);
            };

            $scope.add_problem_list = function (form) {

                form.user_id = $scope.user_id;
                form.patient_id = $scope.patient_id;
                if (form.name && form.labels.length > 0) {
                    problemService.addProblemList(form).then(function (data) {
                        $scope.new_list = {};
                        $scope.new_list.labels = [];
                        toaster.pop('success', 'Done', 'New Problem List added successfully');
                        $scope.create_label_problems_list = false;
                    });
                } else {
                    toaster.pop('error', 'Error', 'Please select name and labels');
                }
            };

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

				var event = getStateChangedEvent($scope.problem);
				$scope.timeline.problems[0].events.splice(-1,1);
				$scope.timeline.problems[0].events.push(event);

				problemService.updateProblemStatus(form).then(function(data){
					var form_problem = {};

					form_problem.patient_id = $scope.patient_id;
					form_problem.timeline_data = $scope.timeline;
					$scope.problem.start_date = convertDateTimeBack($scope.timeline.problems[0].events[$scope.timeline.problems[0].events.length - 1].startTime);;
					problemService.updateStateToPTW(form_problem).then(function(data){
						$scope.timeline_changed = true;
						toaster.pop('success', 'Done', 'Updated Problem Status');
					});
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
					$scope.timeline.problems[0].events[$scope.timeline.problems[0].events.length - 2].startTime = convertDateTime($scope.problem.start_date);
					$scope.timeline_changed = true;
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
                            $scope.show_physician_notes = true;
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

			$scope.get_csrftoken = function(){
                return $cookies.csrftoken;
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
					toaster.pop('success', 'Done', 'Deleted image!');
					$scope.set_authentication_false();
				});
			};


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

			$scope.toggle_physician_notes = function(){

				if($scope.show_physician_notes==true){
					$scope.show_physician_notes = false;
				}else{
					$scope.show_physician_notes = true;
				}
			};


			$scope.refresh_problem_activity=function(){
				problemService.getProblemActivity($scope.problem_id, $scope.current_activity).then(function(data){
					if (data['activities'].length) {
						for (var i=data['activities'].length-1; i>=0; i--){
						    $scope.activities.unshift(data['activities'][i]);
						}
						$scope.current_activity = data['activities'][0].id;
					}
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

			$scope.isInArray = function(array, item) {
				var is_existed = false;
	            angular.forEach(array, function(value, key2) {
	                if (value == item) {
	                    is_existed = true;
	                }
	            });
	            return is_existed;
			};

			// check sharing problem
			$scope.checkSharedProblem = function(problem, sharing_patients) {
				if ($scope.active_user) {

					if ($scope.patient_id == $scope.user_id || $scope.active_user.role!='patient') {
						return true;
					} else {
						var is_existed = false;
			            angular.forEach(sharing_patients, function(p, key) {
			            	if (!is_existed && p.user.id == $scope.user_id) {
		                		is_existed = $scope.isInArray(p.problems, problem.id);
			            	}
			            });

			            return is_existed;
					}
				}
			};
		}); /* End of controller */


})();
