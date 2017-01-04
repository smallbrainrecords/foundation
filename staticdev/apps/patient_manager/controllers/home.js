(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('HomeCtrl', function ($scope, $routeParams, patientService, problemService, encounterService,
                                          ngDialog, sharedService, dataService, toaster, $location, todoService,
                                          prompt, $timeout, CollapseService, $filter, $window, hotkeys) {

            $scope.patient_id = $('#patient_id').val(); // Patients are being managed
            $scope.user_id = $('#user_id').val(); // Current logged in id
            $scope.show_accomplished_todos = false;
            $scope.problem_terms = [];
            $scope.new_problem = {set: false};
            $scope.new_list = {};
            $scope.new_list.labels = [];
            $scope.problem_lists = [];
            $scope.is_home = true;
            $scope.viewMode = 'Year';
            $scope.show_homepage_tab = CollapseService.show_homepage_tab;
            $scope.my_story_tabs = [];
            $scope.selected_tab = null;
            $scope.new_data_type = {};
            $scope.show_add_new_data_type = false;
            $scope.datas = [];
            $scope.show_previous_entries = false;
            $scope.show_add_my_story_tab = false;
            $scope.new_tab = {};
            $scope.new_tab.private = true;
            $scope.new_tab.all_patients = true;
            $scope.show_add_my_story_text = false;
            $scope.new_text = {};
            $scope.new_text.private = true;
            $scope.new_text.all_patients = true;
            $scope.show_edit_my_story_tab = false;

            // Hot key configuration
            hotkeys.add({
                combo: 'ctrl+p',
                description: 'Go to Problem tab',
                callback: function () {
                    $scope.show_homepage_tab = 'problems';
                }
            });

            hotkeys.add({
                combo: 'ctrl+s',
                description: 'Go to My story tab',
                callback: function () {
                    $scope.show_homepage_tab = 'mystory';
                }
            });

            hotkeys.add({
                combo: 'ctrl+d',
                description: 'Go to Data tab',
                callback: function () {
                    $scope.show_homepage_tab = 'data';
                }
            });

            hotkeys.add({
                combo: 'ctrl+m',
                description: 'Go to Medication tab',
                callback: function () {
                    $scope.show_homepage_tab = 'medication';
                }
            });

            hotkeys.add({
                combo: 'ctrl+shift+p',
                description: 'Add new problem',
                callback: function () {
                    $scope.show_homepage_tab = 'problems';
                    $scope.show_homepage_tab = 'problems';
                }
            });

            /**
             * Default graph view mode: Year
             * Available view mode:
             * Week - Month - Year - All
             * @type {string}
             */
            $scope.$watch("viewMode", function (newVal, oldVal) {
                if (newVal != oldVal) {
                    angular.forEach($scope.datas, function (data, key) {
                        // Default graph type
                        if (data.graph == null || data.graph == undefined)
                            data.graph = 'Line';

                        // Temporary data using for generate graph
                        var tmpData = angular.copy(data);
                        // Sorting before processing
                        _.map(tmpData.observation_components, function (item, key) {
                            item.observation_component_values = dataService.updateViewMode($scope.viewMode, item.observation_component_values);

                            // Sorting before generating
                            item.observation_component_values = $filter('orderBy')(item.observation_component_values, "effective_datetime");
                        });
                        data.chartData = dataService.generateChartData(tmpData);
                        data.chartLabel = dataService.generateChartLabel(tmpData);
                    });
                }
            });

            $scope.$watch('files', function () {
                if ($scope.files != undefined)
                    sharedService.uploadDocument($scope.files, $scope.user_id, $scope.patient_id, $scope.fileUploadSuccess);
            });

            $scope.$on('portrait_image_updated', function (event, args) {
                $scope.patient_info = args.data;
            });

            //INITIALIZE DATA
            patientService.fetchActiveUser().then(function (data) {
                // Logged in user profile in Django authentication system
                $scope.active_user = data['user_profile'];
            });

            /*
             *   medication
             */
            patientService.getMedications($scope.patient_id).then(function (data) {
                if (data['success'] == true) {
                    $scope.medications = data['info'];
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });

            // Documentation
            patientService.getDocuments($scope.patient_id).then(function (data) {
                if (data['success'] == true) {
                    $scope.documents = data['info'];
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });

            todoService.fetchTodoMembers($scope.patient_id).then(function (data) {
                $scope.members = data['members'];
            });

            todoService.fetchLabels($scope.patient_id).then(function (data) {
                $scope.labels = data['labels'];
            });

            problemService.fetchLabels($scope.patient_id, $scope.user_id).then(function (data) {
                $scope.problem_labels = data['labels'];
            });

            problemService.fetchLabeledProblemList($scope.patient_id, $scope.user_id).then(function (data) {
                $scope.problem_lists = data['problem_lists'];
                $scope.problems_ready = true;
            });

            patientService.fetchPatientTodos($scope.patient_id).then(function (data) {
                $scope.pending_todos = data['pending_todos'];
                $scope.accomplished_todos = data['accomplished_todos'];
                $scope.problem_todos = data['problem_todos'];
                $scope.todos_ready = true;
            });

            patientService.fetchPatientInfo($scope.patient_id).then(function (data) {
                $scope.patient_info = data['info'];
                $scope.problems = data['problems'];
                $scope.inactive_problems = data['inactive_problems'];
                $scope.goals = data['goals'];
                $scope.completed_goals = data['completed_goals'];

                $scope.encounters = data['encounters'];
                $scope.favorites = data['favorites'];
                $scope.most_recent_encounter_summaries = data['most_recent_encounter_summaries'];
                $scope.most_recent_encounter_related_problems = data['most_recent_encounter_related_problems'];
                $scope.shared_patients = data['shared_patients'];
                $scope.sharing_patients = data['sharing_patients'];
                $scope.acutes = data['acutes_list'];
                $scope.chronics = data['chronics_list'];

                // problem timeline
                $scope.fetchTimeLineProblem(data);


                var tmpListProblem = $scope.problems;

                $scope.sortingLogProblem = [];
                $scope.sortedProblem = false;
                $scope.draggedProblem = false;
                $scope.sortableOptionsProblem = {
                    update: function (e, ui) {
                        $scope.sortedProblem = true;
                    },
                    start: function () {
                        $scope.draggedProblem = true;
                    },
                    stop: function (e, ui) {
                        // this callback has the changed model
                        if ($scope.sortedProblem) {
                            $scope.sortingLogProblem = [];
                            tmpListProblem.map(function (i) {
                                $scope.sortingLogProblem.push(i.id);
                            });
                            var form = {};

                            form.problems = $scope.sortingLogProblem;
                            form.patient_id = $scope.patient_id;

                            patientService.updateProblemOrder(form).then(function (data) {
                                toaster.pop('success', 'Done', 'Updated Problem Order');
                            });
                        }
                        $scope.sortedProblem = false;
                        $timeout(function () {
                            $scope.draggedProblem = false;
                        }, 100);
                    }
                }
            });

            patientService.fetchPainAvatars($scope.patient_id).then(function (data) {
                $scope.pain_avatars = data['pain_avatars'];
            });

            patientService.getMyStory($scope.patient_id).then(function (data) {
                if (data['success'] == true) {
                    $scope.my_story_tabs = data['info'];
                    $scope.selected_tab = $scope.my_story_tabs[0];
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });

            patientService.getDatas($scope.patient_id).then(function (data) {
                if (data['success'] == true) {
                    $scope.datas = data['info'];

                    // TODO: DRY
                    angular.forEach($scope.datas, function (data, key) {
                        // Default graph type
                        if (data.graph == null || data.graph == undefined)
                            data.graph = 'Line';

                        // Temporary data using for generate graph
                        var tmpData = angular.copy(data);
                        // Sorting before processing
                        _.map(tmpData.observation_components, function (item, key) {
                            item.observation_component_values = dataService.updateViewMode($scope.viewMode, item.observation_component_values);

                            // Sorting before generating
                            item.observation_component_values = $filter('orderBy')(item.observation_component_values, "effective_datetime");
                        });
                        data.chartData = dataService.generateChartData(tmpData);
                        data.chartLabel = dataService.generateChartLabel(tmpData);

                        data.chartSeries = dataService.generateChartSeries(tmpData);
                        data.mostRecentValue = dataService.generateMostRecentValue(tmpData);

                        // TODO: Manipulate DOM manually and inside JS code. Need to refine this
                        if (data.name == 'weight') {
                            // $scope.vitals.weight = data;
                            var dom = '<a href="#/data/' + data.id + '">W:' + data.mostRecentValue + '</a>';
                            $("#vitals_weight").html(dom);
                        }
                        if (data.name == 'body temperature') {
                            // $scope.vitals.body_temperature = data;
                            var dom = '<a href="#/data/' + data.id + '">T:' + data.mostRecentValue + '</a>';
                            $("#vitals_body_temperature").html(dom);
                        }

                        if (data.name == 'blood pressure') {
                            // $scope.vitals.blood_pressure = data;
                            var dom = '<a href="#/data/' + data.id + '">BP:' + data.mostRecentValue + '</a>';
                            $("#vitals_blood_pressure").html(dom);
                        }
                        if (data.name == 'heart rate') {
                            // $scope.vitals.heart_rate = data;
                            var dom = '<a href="#/data/' + data.id + '">P:' + data.mostRecentValue + '</a>';
                            $("#vitals_heart_rate ").html(dom);
                        }
                    });

                    if ($scope.active_user) {
                        if ($scope.active_user.role == 'patient') {
                            $scope.mostCommonData = dataService.generateMostCommonData($scope.datas);
                        }

                        if ($scope.active_user.role == 'nurse') {
                            $scope.mostCommonData = [];
                            angular.forEach($scope.datas, function (data, key) {
                                if (data.name == 'weight') {
                                    data.ph = 'W'
                                    $scope.mostCommonData.push(data);
                                }
                                if (data.name == 'body temperature') {
                                    data.ph = 'T'
                                    $scope.mostCommonData.push(data);
                                }
                                if (data.name == 'respiratory rate') {
                                    data.ph = 'RR'
                                    $scope.mostCommonData.push(data);
                                }

                                if (data.name == 'blood pressure') {
                                    data.ph = 'BP'
                                    $scope.mostCommonData.push(data);
                                }
                                if (data.name == 'heart rate') {
                                    data.ph = 'pulse'
                                    $scope.mostCommonData.push(data);
                                }
                                angular.forEach(data.observation_components, function (component, component_key) {
                                    if (component.component_code == '6301-6') {
                                        data.ph = 'INR'
                                        $scope.mostCommonData.push(data);
                                    }
                                });
                            });
                        }
                    }

                    var tmpListData = $scope.datas;
                    $scope.sortingLogData = [];
                    $scope.sortedData = false;
                    $scope.draggedData = false;
                    $scope.sortableOptionsData = {
                        update: function (e, ui) {
                            $scope.sortedData = true;
                        },
                        start: function () {
                            $scope.draggedData = true;
                        },
                        stop: function (e, ui) {
                            // this callback has the changed model
                            if ($scope.sortedData) {
                                $scope.sortingLogData = [];
                                tmpListData.map(function (i) {
                                    $scope.sortingLogData.push(i.id);
                                });
                                var form = {};

                                form.datas = $scope.sortingLogData;
                                form.patient_id = $scope.patient_id;

                                patientService.updateDataOrder(form).then(function (data) {
                                    toaster.pop('success', 'Done', 'Updated Data Order');
                                });
                            }
                            $scope.sortedData = false;
                            $timeout(function () {
                                $scope.draggedData = false;
                            }, 100);
                        }
                    };

                    /*
                     * open data page
                     */
                    $scope.open_data = function (data) {
                        if (!$scope.draggedData) {
                            var form = {};
                            form.patient_id = $scope.patient_id;
                            form.observation_id = data.id;
                            patientService.trackDataClickEvent(form).then(function (data) {

                            });
                            $location.path('/data/' + data.id);
                        }
                    };

                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });

            // METHOD DEFINITION

            $scope.timelineSave = function (newData) {
                var form = {};

                form.patient_id = $scope.patient_id;
                form.timeline_data = newData;

                problemService.updateByPTW(form).then(function (data) {

                    toaster.pop('success', 'Done', 'Updated Problems');
                });
            };

            $scope.fetchTimeLineProblem = function (data) {

                patientService.fetchTimeLineProblem($scope.patient_id).then(function (data2) {
                    var timeline_problems = [];
                    angular.forEach(data2['timeline_problems'], function (value, key) {

                        if (value.problem_segment.length !== undefined && value.problem_segment.length > 0) {
                            var timeline_problem = parseTimelineWithSegment(value);
                        } else {
                            var timeline_problem = parseTimelineWithoutSegment(value);
                        }

                        if ($scope.checkSharedProblem(timeline_problem, $scope.sharing_patients))
                            timeline_problems.push(timeline_problem);
                    });

                    $scope.timeline = {
                        Name: data['info']['user']['first_name'] + data['info']['user']['last_name'],
                        birthday: convertDateTimeBirthday(data['info']['date_of_birth']),
                        problems: timeline_problems
                    };

                    $scope.timeline_ready = true;
                    $scope.timeline_changed = [{changing: new Date().getTime()}];
                });
            };

            $scope.update_patient_summary = function () {

                var form = {
                    'patient_id': $scope.patient_id,
                    'summary': $scope.patient_info.summary
                };

                patientService.updatePatientSummary(form).then(function (data) {
                    toaster.pop('success', 'Done', 'Patient summary updated!');
                });

            };

            $scope.toggle_accomplished_todos = function () {

                var flag = $scope.show_accomplished_todos;

                // TODO: Refactor/Simplify block code later
                if (flag == true) {
                    flag = false;
                } else {
                    flag = true;
                }

                $scope.show_accomplished_todos = flag;
            };

            $scope.add_goal = function (form) {

                form.patient_id = $scope.patient_id;
                patientService.addGoal(form).then(function (data) {


                    var new_goal = data['goal'];

                    $scope.goals.push(new_goal);

                    toaster.pop('success', "Done", "New goal created successfully!");
                    console.log('pop');

                });

            };

            $scope.add_todo = function (form) {

                form.patient_id = $scope.patient_id;

                prompt({
                    title: 'Add Due Date',
                    message: 'Enter due date',
                    input: true,
                    label: 'Due Date',
                }).then(function (due_date) {
                    if (moment(due_date, "MM/DD/YYYY", true).isValid()) {
                        form.due_date = due_date;
                    } else if (moment(due_date, "M/D/YYYY", true).isValid()) {
                        form.due_date = moment(due_date, "M/D/YYYY").format("MM/DD/YYYY");
                    } else if (moment(due_date, "MM/YYYY", true).isValid()) {
                        form.due_date = moment(due_date, "MM/YYYY").date(1).format("MM/DD/YYYY");
                    } else if (moment(due_date, "M/YYYY", true).isValid()) {
                        form.due_date = moment(due_date, "M/YYYY").date(1).format("MM/DD/YYYY");
                    } else if (moment(due_date, "MM/DD/YY", true).isValid()) {
                        form.due_date = moment(due_date, "MM/DD/YY").format("MM/DD/YYYY");
                    } else if (moment(due_date, "M/D/YY", true).isValid()) {
                        form.due_date = moment(due_date, "M/D/YY").format("MM/DD/YYYY");
                    } else if (moment(due_date, "MM/YY", true).isValid()) {
                        form.due_date = moment(due_date, "MM/YY").date(1).format("MM/DD/YYYY");
                    } else if (moment(due_date, "M/YY", true).isValid()) {
                        form.due_date = moment(due_date, "M/YY").date(1).format("MM/DD/YYYY");
                    } else {
                        toaster.pop('error', 'Error', 'Please enter a valid date!');
                        return false;
                    }

                    patientService.addToDo(form).then(function (data) {
                        var new_todo = data['todo'];
                        $scope.pending_todos.push(new_todo);
                        $scope.problem_todos.push(new_todo);

                        $scope.new_todo = {};

                        toaster.pop('success', 'Done', 'New Todo added successfully');
                    });
                }, function () {
                    patientService.addToDo(form).then(function (data) {
                        var new_todo = data['todo'];
                        $scope.pending_todos.push(new_todo);
                        $scope.problem_todos.push(new_todo);

                        $scope.new_todo = {};

                        toaster.pop('success', 'Done', 'New Todo added successfully');
                    });
                });
            };

            $scope.$watch('problem_term', function (newVal, oldVal) {

                if (newVal == undefined) {
                    return false;
                }

                $scope.unset_new_problem();
                if (newVal.length > 2) {
                    patientService.listTerms(newVal).then(function (data) {
                        $scope.problem_terms = data;
                    });
                } else {
                    $scope.problem_terms = [];
                }
            });

            $scope.set_new_problem = function (problem) {

                $scope.new_problem.set = true;
                $scope.new_problem.active = problem.active;
                $scope.new_problem.term = problem.term;
                $scope.new_problem.code = problem.code;


            };

            $scope.unset_new_problem = function () {
                $scope.new_problem.set = false;
            };


            $scope.add_problem = function () {

                var c = confirm("Are you sure?");

                if (c == false) {
                    return false;
                }

                var form = {};
                form.patient_id = $scope.patient_id;
                form.term = $scope.new_problem.term;
                form.code = $scope.new_problem.code;
                form.active = $scope.new_problem.active;

                patientService.addProblem(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'New Problem added successfully');
                        $scope.problems.push(data['problem']);
                        $scope.problem_term = '';
                        $scope.unset_new_problem();
                        /* Not-angular-way */
                        $('#problemTermInput').focus();

                    } else if (data['success'] == false) {
                        alert(data['msg']);
                    } else {
                        alert("Something went wrong");
                    }


                });


            };

            $scope.add_new_problem = function (problem_term) {
                if (problem_term == '' || problem_term == undefined) {
                    return false;
                }

                var c = confirm("Are you sure?");

                if (c == false) {
                    return false;
                }


                var form = {};
                form.patient_id = $scope.patient_id;
                form.term = problem_term;

                patientService.addProblem(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'New Problem added successfully');
                        $scope.problems.push(data['problem']);
                        $scope.problem_term = '';
                        $scope.unset_new_problem();
                        /* Not-angular-way */
                        $('#problemTermInput').focus();
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', data['msg']);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong');
                    }
                });
            };

            $scope.add_new_common_problem = function (problem, type) {
                var form = {};
                form.patient_id = $scope.patient_id;
                form.cproblem = problem;
                form.type = type;

                patientService.addCommonProblem(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'New Problem added successfully');
                        $scope.problems.push(data['problem']);
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', data['msg']);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong');
                    }
                });
            };

            $scope.update_todo_status = function (todo) {

                patientService.updateTodoStatus(todo).then(function (data) {

                    if (data['success'] == true) {
                        $scope.pending_todos = data['pending_todos'];
                        $scope.accomplished_todos = data['accomplished_todos'];
                        toaster.pop('success', "Done", "Updated Todo status !");
                    } else {
                        alert("Something went wrong!");
                    }

                });

            };

            $scope.open_problem = function (problem) {

                if (!$scope.draggedProblem) {
                    $location.path('/problem/' + problem.id);
                }
            };


            $scope.permitted = function (permissions) {

                if ($scope.active_user == undefined) {
                    return false;
                }

                var user_permissions = $scope.active_user.permissions;

                for (var key in permissions) {

                    if (user_permissions.indexOf(permissions[key]) < 0) {
                        return false;
                    }
                }

                return true;

            };


            // label problem list
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

            $scope.set_collapse = function (list) {
                if (list.rename == false)
                    list.collapse = !list.collapse;
            };

            $scope.delete_list = function (list) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a problem list is forever. There is no undo."
                }).then(function (result) {
                    problemService.deleteProblemList(list).then(function (data) {
                        var index = $scope.problem_lists.indexOf(list);
                        $scope.problem_lists.splice(index, 1);
                        toaster.pop('success', 'Done', 'Problem List removed successfully');
                    });
                }, function () {
                    return false;
                });
            };

            $scope.rename_list = function (list) {
                if (list.name) {
                    problemService.renameProblemList(list).then(function (data) {
                        list.rename = false;
                        toaster.pop('success', 'Done', 'Problem List renamed successfully');
                    });
                } else {
                    toaster.pop('error', 'Error', 'Please input name!');
                }

            };

            $scope.update_problem_list_note = function (list) {

                var form = {
                    'list_id': list.id,
                    'note': list.note
                };

                problemService.updateProblemListNote(form).then(function (data) {
                    toaster.pop('success', 'Done', 'Problem list note updated!');
                });

            };

            $scope.check_problem_list_authenticated = function (list) {
                var is_existed = false;
                angular.forEach(list.problems, function (value, key) {
                    if (!value.authenticated) {
                        is_existed = true;
                    }
                });
                return is_existed;
            };

            $scope.check_problem_list_controlled = function (list) {
                var is_existed = false;
                angular.forEach(list.problems, function (value, key) {
                    if (!value.is_controlled) {
                        is_existed = true;
                    }
                });
                return is_existed;
            };

            $scope.inArray = function (array, item) {
                var is_existed = false;
                angular.forEach(array, function (list, key2) {
                    angular.forEach(list.problems, function (value, key) {
                        if (value.id == item.id) {
                            is_existed = true;
                        }
                    });
                });
                return is_existed;
            };

            $scope.isInArray = function (array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value == item) {
                        is_existed = true;
                    }
                });
                return is_existed;
            };

            $scope.checkSharedProblem = function (problem, sharing_patients) {
                if ($scope.patient_id == $scope.user_id || ($scope.active_user.hasOwnProperty('role') && $scope.active_user.role != 'patient')) {
                    return true;
                } else {
                    var is_existed = false;
                    angular.forEach(sharing_patients, function (p, key) {
                        if (!is_existed && p.user.id == $scope.user_id) {
                            is_existed = $scope.isInArray(p.problems, problem.id);
                        }
                    });

                    return is_existed;
                }
            };

            // note on header of page
            $scope.update_patient_note = function () {

                var form = {
                    'patient_id': $scope.patient_id,
                    'note': $scope.patient_info.note
                };

                patientService.updatePatientNote(form).then(function (data) {
                    toaster.pop('success', 'Done', 'Patient note updated!');
                });

            };

            // encounter

            $scope.unmarkFavoriteEvent = function (encounter_event) {
                var form = {};
                form.encounter_event_id = encounter_event.id;
                form.is_favorite = false;
                encounterService.markFavoriteEvent(form).then(function (data) {
                    $scope.favorites.splice($scope.favorites.indexOf(encounter_event), 1);
                    toaster.pop('success', 'Done', 'Unmarked favorite!');
                });
            };

            $scope.nameFavoriteEvent = function (encounter_event) {
                var form = {};
                form.encounter_event_id = encounter_event.id;
                form.name_favorite = encounter_event.name_favorite;
                encounterService.nameFavoriteEvent(form).then(function (data) {
                    encounter_event.is_named = false;
                    toaster.pop('success', 'Done', 'Named favorite!');
                });
            };


            /**
             * Callback when user choose new cover image from computer
             */
            $scope.on_cover_picture_upload = function (file) {
                var form = {};
                form.user_id = $scope.patient_info.user.id;
                form.phone_number = $scope.patient_info.phone_number;
                form.sex = $scope.patient_info.sex;
                form.role = $scope.patient_info.role;
                form.summary = $scope.patient_info.summary;
                form.date_of_birth = $scope.patient_info.date_of_birth;
                var files = {cover_image: file[0]};

                patientService.updateProfile(form, files).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Patient updated!');
                        $scope.patient_info = data['info'];
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Please fill valid data');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }

                });
            };

            /**
             * Callback when user choosing thee reposition action
             */
            $scope.on_cover_picture_reposition = function () {
                $scope.is_reposition_flag = true;
                console.log("On cover image starting reposition .....");
            };


            /**
             * Callback when user click on remove cover image
             */
            $scope.on_cover_picture_remove = function () {
                alert("Function under-construction we will update asap");
            };


            /**
             * Update profile picture handler
             * Open prompt require user choosing upload method
             */
            $scope.updateProfilePicture = function () {
                ngDialog.open({
                    controller: 'PortraitUpdCtrl',
                    template: '/static/apps/patient_manager/partials/modals/update_profile_picture.html',
                    scope: $scope
                });
            };

            /*
             *   handle cache homepage tabs
             */

            $scope.change_homepage_tab = function (tab) {
                CollapseService.ChangeHomepageTab(tab);
                $scope.show_homepage_tab = CollapseService.show_homepage_tab;
                if ($scope.show_homepage_tab == "data") {
                    var form = {};
                    form.patient_id = $scope.patient_id;
                    patientService.trackDataClickEvent(form).then(function (data) {
                    });
                } else {
                    $timeout(function () {
                        $scope.show_homepage_tab = CollapseService.show_homepage_tab;
                    }, 500);
                }
            };

            /*
             *   get my story data
             */


            /*
             *   toggle add my story tab
             */

            $scope.toggle_add_my_story_tab = function () {
                $scope.show_add_my_story_tab = !$scope.show_add_my_story_tab;
            };


            $scope.add_my_story_tab = function (new_tab) {
                if (new_tab.name) {
                    var form = {};
                    form.name = new_tab.name;
                    if ($scope.active_user.role == 'patient')
                        form.private = new_tab.private;
                    if ($scope.active_user.role == 'admin' || $scope.active_user.role == 'physician')
                        form.all_patients = new_tab.all_patients;
                    form.patient_id = $scope.patient_id;
                    patientService.addMyStoryTab(form).then(function (data) {
                        if (data['success'] == true) {
                            $scope.my_story_tabs.push(data['tab']);
                            new_tab.name = '';
                            new_tab.private = true;
                            new_tab.all_patients = true;
                            toaster.pop('success', "Done", "New tab created successfully!");
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
                } else {
                    toaster.pop('error', "Error", "Please input name!");
                }
            };

            /*
             *   toggle view my story tab
             */

            $scope.view_my_story_tab = function (tab) {
                var form = {};
                form.patient_id = $scope.patient_id;
                form.tab_id = tab.id;
                patientService.trackTabClickEvent(form).then(function (data) {
                });
                $scope.selected_tab = tab;
                $scope.show_edit_my_story_tab = false;
            };

            /*
             *   toggle add my story text
             */

            $scope.toggle_add_my_story_text = function () {
                $scope.show_add_my_story_text = !$scope.show_add_my_story_text;
            };


            $scope.add_my_story_text = function (tab, new_text) {
                var form = {};
                form.name = new_text.name;
                form.text = new_text.text;
                if ($scope.active_user.role == 'patient')
                    form.private = new_text.private;
                if (tab.is_all && ($scope.active_user.role == 'admin' || $scope.active_user.role == 'physician'))
                    form.all_patients = new_text.all_patients;
                form.concept_id = new_text.concept_id;
                form.patient_id = $scope.patient_id;
                form.tab_id = tab.id;
                patientService.addMyStoryText(form).then(function (data) {
                    if (data['success'] == true) {
                        tab.my_story_tab_components.push(data['component']);
                        new_text.name = '';
                        new_text.text = '';
                        new_text.concept_id = '';
                        new_text.private = true;
                        new_text.all_patients = true;
                        toaster.pop('success', "Done", "New Text Component created successfully!");
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            };

            /*
             *   toggle edit my story tab
             */

            $scope.edit_my_story_tab = function () {
                $scope.show_edit_my_story_tab = !$scope.show_edit_my_story_tab;
            };

            /*
             *   delete my story tab
             */
            $scope.delete_my_story_tab = function (selected_tab) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a tab is forever. There is no undo."
                }).then(function (result) {
                    patientService.deleteMyStoryTab($scope.patient_id, selected_tab.id).then(function (data) {
                        if (data['success'] == true) {
                            var index = $scope.my_story_tabs.indexOf(selected_tab);
                            $scope.my_story_tabs.splice(index, 1);

                            if ($scope.my_story_tabs.length > 0)
                                $scope.selected_tab = $scope.my_story_tabs[0];
                            $scope.show_edit_my_story_tab = false;
                            toaster.pop('success', "Done", "Deleted tab successfully!");
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
                }, function () {
                    return false;
                });
            };

            $scope.save_my_story_tab = function (selected_tab) {
                if (selected_tab.name) {
                    var form = {};
                    form.name = selected_tab.name;
                    form.tab_id = selected_tab.id;
                    form.patient_id = $scope.patient_id;
                    patientService.saveMyStoryTab(form).then(function (data) {
                        if (data['success'] == true) {
                            $scope.show_edit_my_story_tab = false;
                            toaster.pop('success', "Done", "Saved tab successfully!");
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
                } else {
                    toaster.pop('error', "Error", "Please input name!");
                }
            };

            /*
             *   delete my story tab
             */
            $scope.delete_my_story_text = function (component) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a text component is forever. There is no undo."
                }).then(function (result) {
                    patientService.deleteMyStoryText($scope.patient_id, component.id).then(function (data) {
                        if (data['success'] == true) {
                            var index = $scope.selected_tab.my_story_tab_components.indexOf(component);
                            $scope.selected_tab.my_story_tab_components.splice(index, 1);

                            toaster.pop('success', "Done", "Deleted text component successfully!");
                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
                }, function () {
                    return false;
                });
            };

            $scope.save_my_story_text = function (component) {
                var form = {};
                form.name = component.name;
                form.concept_id = component.concept_id;
                form.component_id = component.id;
                form.patient_id = $scope.patient_id;
                patientService.saveMyStoryText(form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', "Done", "Saved text component successfully!");
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            };

            $scope.change_component_text = function (component, entry, oldText) {
                var form = {};
                form.text = entry.text;
                form.component_id = component.id;
                form.entry_id = entry.id;
                form.patient_id = $scope.patient_id;
                patientService.saveMyStoryTextEntry(form).then(function (data) {
                    if (data['success'] == true) {
                        component.text_component_entries.unshift(data['entry']);
                        if (typeof oldText !== 'undefined')
                            entry.text = oldText;
                        toaster.pop('success', "Done", "Saved text component successfully!");
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            };


            $scope.see_previous_entries = function () {
                $scope.show_previous_entries = !$scope.show_previous_entries;
            };

            $scope.checkSharedMyStory = function () {
                if ($scope.active_user) {
                    if ($scope.patient_id == $scope.user_id || $scope.active_user.role != 'patient') {
                        return true;
                    } else {
                        var is_shared = false;
                        angular.forEach($scope.sharing_patients, function (user, key) {
                            if (user.id == $scope.active_user.id && user.is_my_story_shared) {
                                is_shared = true;
                            }
                        });
                        return is_shared;
                    }
                }
                return false;
            };


            $scope.toggle_add_new_data_type = function () {
                $scope.show_add_new_data_type = !$scope.show_add_new_data_type;
            };

            $scope.add_new_data_type = function (new_data_type) {
                var form = {};
                form.name = new_data_type.name;
                form.code = new_data_type.code;
                form.unit = new_data_type.unit;
                form.color = new_data_type.color;
                form.patient_id = $scope.patient_id;
                patientService.addNewDataType(form).then(function (data) {
                    if (data['success'] == true) {
                        $scope.datas.push(data['observation']);
                        new_data_type.name = '';
                        new_data_type.code = '';
                        new_data_type.unit = '';
                        new_data_type.color = '';
                        toaster.pop('success', "Done", "New Data Type created successfully!");
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            };

            $scope.check_has_data_loinc_code = function (datas, code) {
                var is_inr = false;
                angular.forEach(datas, function (data, key) {
                    angular.forEach(data.observation_components, function (component, key2) {
                        if (component.component_code == code) {
                            is_inr = true;
                        }
                    });
                });
                return is_inr;
            };

            $scope.add_bfdi_value = function (component) {
                var new_data = {};
                new_data.datetime = moment().format("MM/DD/YYYY HH:mm");

                new_data.value = component.new_value;
                dataService.addData($scope.patient_id, component.id, new_data).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Added data!');
                        angular.forEach($scope.datas, function (sdata, data_key) {
                            angular.forEach(sdata.observation_components, function (scomponent, component_key) {
                                if (scomponent.id == component.id) {
                                    scomponent.observation_component_values.push(data['value']);
                                }
                            });

                            // Default graph type
                            if (sdata.graph == null || sdata.graph == undefined)
                                sdata.graph = 'Line';

                            // Temporary data using for generate graph
                            var tmpData = angular.copy(sdata);
                            // Sorting before processing
                            _.map(tmpData.observation_components, function (item, key) {
                                item.observation_component_values = dataService.updateViewMode($scope.viewMode, item.observation_component_values);

                                // Sorting before generating
                                item.observation_component_values = $filter('orderBy')(item.observation_component_values, "effective_datetime");
                            });
                            sdata.chartData = dataService.generateChartData(tmpData);
                            sdata.chartLabel = dataService.generateChartLabel(tmpData);
                            sdata.mostRecentValue = dataService.generateMostRecentValue(tmpData);
                        });
                        component.new_value = '';
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            };

            $scope.fileUploadSuccess = function (resp) {
                $window.open('/#/manage/tag_document/' + resp.data.document, '_blank');
            };

            //Anonymous function (will be hoisting)
            function convertDateTime(problem) {
                if (problem.start_date) {
                    var dateTime = problem.start_date;
                    var date = dateTime.split("/");
                    var yyyy = date[2];
                    var mm = date[0];
                    var dd = date[1];

                    if (problem.start_time) {
                        return dd + '/' + mm + '/' + yyyy + ' ' + problem.start_time;
                    }

                    return dd + '/' + mm + '/' + yyyy + ' 00:00:00';
                }
                return '30/11/1970 00:00:00';
            }

            function convertDateTimeBirthday(dateTime) {
                if (dateTime) {
                    var date = dateTime.split("/");
                    var yyyy = date[2];
                    var mm = date[0];
                    var dd = date[1];

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
                var temp;

                angular.forEach(problem.problem_segment, function (value, key) {
                    event = {};
                    event['event_id'] = value.event_id;
                    event['state'] = getTimelineWidgetState(value);

                    if (key == 0) {
                        event['startTime'] = convertDateTime(problem);
                    } else {
                        event['startTime'] = convertDateTime(temp);
                    }
                    temp = value;
                    events.push(event);
                });

                if (temp) {
                    events.push({
                        event_id: new Date().getTime(),
                        startTime: convertDateTime(temp),
                        state: getTimelineWidgetState(problem)
                    });
                }

                var timeline_problem = {
                    'name': problem.problem_name,
                    'id': problem.id,
                    events: events
                };

                return timeline_problem;
            }

            function copyToClipboard(text) {
                var $temp = $("<textarea/>");
                $("body").append($temp);
                $temp.val(text).select();
                document.execCommand("copy");
                $temp.remove();
            }

            $(window).keydown(function (event) {
                if (event.ctrlKey && event.keyCode == 67 && $location.path() == '/') {
                    var text = '';

                    // encounter copy
                    if ($scope.most_recent_encounter_summaries.length > 0) {
                        text += "All the encounter summaries from the most recent encounter: \r\n";
                        angular.forEach($scope.most_recent_encounter_summaries, function (value, key) {
                            var container = $("<div/>");
                            container.append(value);

                            text += container.text() + '\r\n';
                        });
                        text += '\r\n';
                    }

                    if ($scope.most_recent_encounter_related_problems.length > 0) {
                        text += "List of related problems : \r\n";
                        angular.forEach($scope.most_recent_encounter_related_problems, function (value, key) {
                            text += value.problem_name + '\r\n';
                        });
                        text += '\r\n';
                    }

                    if ($scope.pending_todos.length > 0) {
                        text += "List of all active todos : \r\n";
                        angular.forEach($scope.pending_todos, function (value, key) {
                            text += value.todo + '\r\n';
                        });
                    }

                    copyToClipboard(text);
                    event.preventDefault();
                }

                if (event.ctrlKey && event.keyCode == 68 && $location.path() == '/') {
                    event.preventDefault();
                    $scope.change_homepage_tab('data');
                }

                if (event.ctrlKey && event.keyCode == 83 && $location.path() == '/') {
                    event.preventDefault();
                    $scope.change_homepage_tab('mystory');
                }
            });
        });
    /* End of controller */

})();

