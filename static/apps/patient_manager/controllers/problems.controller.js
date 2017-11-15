(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('ProblemsCtrl', function ($scope, $routeParams, $interval, patientService, problemService, sharedService,
                                              $filter, ngDialog, toaster, todoService, prompt, $cookies, $location,
                                              dataService, medicationService, CollapseService, Upload, $timeout, LABELS, TODO_LIST) {

            $scope.activities = [];
            $scope.availableWidgets = [];
            $scope.change_pinned_data = false;
            $scope.change_pinned_medication = false;
            $scope.change_problem_label = false;
            $scope.create_label_problems_list = false;
            $scope.create_problem_label = false;
            $scope.current_activity = 0;
            $scope.hasAccess = false;
            $scope.history_note_form = {};
            $scope.isOtherPatientNoteShowing = false;
            $scope.loading = true;
            $scope.medications = [];
            $scope.new_list = {};
            $scope.new_list.labels = [];
            $scope.new_problem = {set: false};
            $scope.problem_id = $routeParams.problem_id;
            $scope.problem_label_component = {};
            $scope.problem_terms = [];
            // $scope.problem_todos = [];
            $scope.related_encounters = [];
            $scope.show_accomplished_goals = false;
            $scope.show_accomplished_todos = false;
            $scope.show_other_notes = false;
            $scope.show_physician_notes = false;
            $scope.viewMode = 'Year';
            $scope.wiki_note_form = {};
            $scope.problem_labels_component = LABELS;
            $scope.edit_problem = false;
            $scope.show_inactive_medications = false;
            $scope.showMedicationSearch = false;

            $scope.pending_todos = [];
            $scope.accomplished_todos = [];
            $scope.todoIsLoading = false;
            $scope.pendingTodoPage = 1;
            $scope.accomplishedTodoPage = 1;
            $scope.accomplishedTodoLoaded = false;
            $scope.pendingTodoLoaded = false;
            $scope.encounter_collapse = false;

            // Init hot key binding
            $scope.add_goal = add_goal;
            $scope.add_history_note = add_history_note;
            $scope.add_new_list_label = add_new_list_label;
            $scope.add_problem_list = add_problem_list;
            $scope.add_todo = addTodo;
            $scope.add_wiki_note = add_wiki_note;
            $scope.change_effected_problem = change_effected_problem;
            $scope.change_effecting_problem = change_effecting_problem;
            $scope.change_new_problem_name = change_new_problem_name;
            $scope.change_problem_name = change_problem_name;
            $scope.changeProblemLabel = changeProblemLabel;
            $scope.changeView = changeView;
            $scope.checkSharedProblem = checkSharedProblem;
            $scope.close_change_data = close_change_data;
            $scope.close_change_medication = close_change_medication;
            $scope.close_change_problem_label = close_change_problem_label;
            $scope.close_create_label_problems_list = close_create_label_problems_list;
            $scope.close_create_problem_label = close_create_problem_label;
            $scope.data_pin_to_problem = data_pin_to_problem;
            $scope.delete_problem = delete_problem;
            $scope.delete_problem_image = delete_problem_image;
            $scope.deleteEditProblemLabel = deleteEditProblemLabel;
            $scope.editProblemLabel = editProblemLabel;
            $scope.goToMedicationTab = goToMedicationTab;
            $scope.id_exists = id_exists;
            $scope.isInArray = isInArray;
            $scope.medication_pin_to_problem = medication_pin_to_problem;
            $scope.open_change_data = open_change_data;
            $scope.open_change_medication = open_change_medication;
            $scope.open_change_problem_label = open_change_problem_label;
            $scope.open_create_label_problems_list = openCreateLabelProblemsList;
            $scope.open_create_problem_label = open_create_problem_label;
            $scope.open_data = open_data;
            $scope.open_image_box = open_image_box;
            $scope.open_image_upload_box = open_image_upload_box;
            $scope.open_medication = open_medication;
            $scope.permitted = permitted;
            $scope.problem_name_changed = problem_name_changed;
            $scope.refresh_problem_activity = refresh_problem_activity;
            $scope.saveCreateProblemLabel = saveCreateProblemLabel;
            $scope.saveEditProblemLabel = saveEditProblemLabel;
            $scope.selectEditProblemLabelComponent = selectEditProblemLabelComponent;
            $scope.selectProblemLabelComponent = selectProblemLabelComponent;
            $scope.set_authentication_false = set_authentication_false;
            $scope.set_new_problem = set_new_problem;
            $scope.timelineSave = timelineSave;
            $scope.toggle_accomplished_goals = toggle_accomplished_goals;
            $scope.toggle_accomplished_todos = toggle_accomplished_todos;
            $scope.toggle_other_notes = toggle_other_notes;
            $scope.toggle_physician_notes = toggle_physician_notes;
            $scope.unset_new_problem = unset_new_problem;
            $scope.update_start_date = update_start_date;
            $scope.addMedication = addMedication;
            $scope.updateStatusCallback = changeTodoList;
            $scope.loadMoreTodo = loadMoreTodo;
            $scope.A1COrderAdded = widgetTodoAdded;
            $scope.A1COrderStatusChanged = widgetTodoStatusChanged;
            $scope.colonCancersOrderAdded = widgetTodoAdded;
            $scope.colonCancersOrderStatusChanged = widgetTodoStatusChanged;
            $scope.INROrderAdded = widgetTodoAdded;
            $scope.INROrderStatusChanged = widgetTodoStatusChanged;

            $scope.$on('todoListUpdated', (event, args) => {
                $scope.pending_todos = patientService.getProblemTodo($scope.problem_id);
                $scope.todoIsLoading = false;
            });

            $scope.$on('todoAdded', (event, args) => {
                $scope.pending_todos = patientService.getProblemTodo($scope.problem_id);
            });

            init();

            function init() {
                $scope.pending_todos = patientService.getProblemTodo($scope.problem_id);

                patientService.fetchProblemInfo($scope.problem_id)
                    .then(function (data) {
                        $scope.loading = false;

                        if (data.success) {
                            // $scope.hasAccess = false;
                            // }
                            $scope.hasAccess = true;

                            $scope.problem = data['info'];

                            $scope.sharing_patients = data['sharing_patients'];

                            // problem time line
                            if ($scope.problem.problem_segment !== undefined && $scope.problem.problem_segment.length > 0) {
                                var timeline_problems = parseTimelineWithSegment($scope.problem);
                            } else {
                                var timeline_problems = parseTimelineWithoutSegment($scope.problem);
                            }

                            $scope.availableWidgets = data['available_widgets'];
                            if (_.contains($scope.availableWidgets, 'a1c')) {
                                problemService.fetchA1c($scope.problem_id).then(function (response) {
                                    $scope.a1c = response['a1c'];
                                });
                            }

                            if (_.contains($scope.availableWidgets, 'colon_cancers')) {
                                problemService.fetchColonCancerss($scope.problem_id).then(function (response) {
                                    $scope.colon_cancers = response['colon_cancers'];
                                });
                            }


                            $scope.timeline = {
                                Name: $scope.patient_info['user']['first_name'] + $scope.patient_info['user']['last_name'],
                                birthday: convertDateTimeBirthday($scope.patient_info['date_of_birth']),
                                problems: timeline_problems
                            };

                            $scope.timeline_ready = true;
                            $scope.timeline_changed = [{changing: new Date().getTime()}];
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

                problemService.trackProblemClickEvent($scope.problem_id);

                // SECONDARY LOADING

                // Wiki note
                problemService.getRelatedWikis($scope.problem_id).then(function (response) {
                    $scope.history_note = response.data['history_note'];
                    if ($scope.history_note != null) {
                        $scope.history_note_form = {
                            note: $scope.history_note.note
                        };
                    }

                    var wiki_notes = response.data['wiki_notes'];
                    $scope.patient_wiki_notes = wiki_notes['patient'];
                    $scope.physician_wiki_notes = wiki_notes['physician'];
                    $scope.other_wiki_notes = wiki_notes['other'];
                });

                // Pinned observation component (aka data)
                problemService.fetchPinToProblem($scope.problem_id).then(function (data) {
                    // TODO: Deprecated check
                    $scope.pins = data['pins'];
                    $scope.problem_pins = data['problem_pins'];
                    $scope.hasPinnedGraph = false;

                    $scope.datas = [];
                    patientService.getDatas($scope.patient_id).then(function (data) {
                        if (data['success']) {
                            $scope.datas = data['info'];
                            angular.forEach($scope.datas, function (data, key) {
                                var is_pin = false;
                                angular.forEach($scope.problem_pins, function (pin, key) {
                                    if (data.id === pin.observation) {
                                        is_pin = true;
                                        $scope.hasPinnedGraph = true;
                                        data.pin_author = pin.author.id;
                                    }
                                });
                                data.pin = is_pin;

                                // Default graph type
                                if (data.graph == null || data.graph === undefined)
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

                                // Unaffected graph option when time range filter changed
                                data.chartSeries = dataService.generateChartSeries(tmpData);
                                data.mostRecentValue = dataService.generateMostRecentValue(tmpData);

                                // TODO: Manipulate DOM manually and inside JS code. Need to refine this
                                if ("weight" === data.name) {
                                    $("#vitals_weight").html(`<a href="#/data/${data.id}">${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue }</a>`);
                                }
                                if ("body temperature" === data.name) {
                                    $("#vitals_body_temperature").html(`<a href="#/data/${data.id}">${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue }</a>`);
                                }
                                if ("blood pressure" === data.name) {
                                    $("#vitals_blood_pressure").html(`<a href="#/data/${data.id}">${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue }</a>`);
                                }
                                if ("heart rate" === data.name) {
                                    $("#vitals_heart_rate ").html(`<a href="#/data/${data.id}">${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue }</a>`);
                                }
                            });

                        } else {
                            toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                        }
                    });
                });

                // Medication TODO 02/03/2017 refactor to problem service
                patientService.getMedications($scope.patient_id).then(function (data) {
                    if (data['success'] == true) {
                        $scope.medications = data['info'];
                        $scope.hasPinnedMedication = false;
                        problemService.fetchMedicationPinToProblem($scope.problem_id).then(function (data) {
                            $scope.medication_pins = data['pins'];
                            angular.forEach($scope.medications, function (medication, key) {
                                var is_pin = false;
                                angular.forEach($scope.medication_pins, function (pin, key) {
                                    if (medication.id == pin.medication.id) {
                                        is_pin = true;
                                        $scope.hasPinnedMedication = true;
                                        medication.pin_author = pin.author.id;
                                    }
                                });
                                medication.pin = is_pin;
                            });
                        });
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });

                // Goal
                problemService.getRelatedGoals($scope.problem_id).then(function (response) {
                    $scope.problem_goals = response.data.goals;
                    $scope.hasAccomplishedGoal = _.pluck(response.data.goals, 'accomplished');
                });

                // Image
                problemService.getRelatedImages($scope.problem_id).then(function (response) {
                    $scope.problem_images = response.data['images'];

                });

                // Effecting & Effected problems
                problemService.getProblemRelationships($scope.problem_id).then(function (response) {
                    $scope.effecting_problems = response.data['effecting_problems'];
                    $scope.effected_problems = response.data['effected_problems'];
                    var patient_problems = response.data['patient_problems'];
                    for (var index in patient_problems) {
                        var id = patient_problems[index].id;
                        if ($scope.id_exists(id, $scope.effecting_problems) == true) {
                            patient_problems[index].effecting = true
                        }

                        if ($scope.id_exists(id, $scope.effected_problems) == true) {
                            patient_problems[index].effected = true
                        }
                    }
                    $scope.patient_problems = patient_problems;
                });

                // Activity
                problemService.getProblemActivity($scope.problem_id, 0).then(function (response) {
                    $scope.activities = response['activities'];
                    if (response['activities'].length) {
                        $scope.current_activity = _.first(response['activities']).id;
                    }
                });

                // Encounter
                problemService.getRelatedEncounters($scope.problem_id).then(function (response) {
                    $scope.related_encounters = response.encounters;
                });

                // Document
                problemService.getRelatedDocuments($scope.problem_id).then(function (response) {
                    $scope.pinned_document = response.data.documents;
                });

                // Watcher & callback
                $scope.$watch('[problem.is_controlled,problem.authenticated, problem.is_active]', function (nV, oV) {

                    if ($scope.loading == true) {
                        return false;
                    }

                    if (angular.equals(oV, [undefined, undefined, undefined]) == true) {
                        return false;
                    }

                    var form = {};

                    form.patient_id = $scope.patient_id;
                    form.problem_id = $scope.problem.id;
                    form.is_controlled = $scope.problem.is_controlled;
                    form.authenticated = $scope.problem.authenticated;
                    form.is_active = $scope.problem.is_active;

                    var event = getStateChangedEvent($scope.problem);
                    $scope.timeline.problems[0].events.splice(-1, 1);
                    $scope.timeline.problems[0].events.push(event);

                    problemService.updateProblemStatus(form).then(function (data) {
                        var form_problem = {};

                        form_problem.patient_id = $scope.patient_id;
                        form_problem.timeline_data = $scope.timeline;
                        $scope.problem.start_date = convertDateTimeBack($scope.timeline.problems[0].events[0].startTime);
                        problemService.updateStateToPTW(form_problem).then(function (data) {
                            toaster.pop('success', 'Done', 'Updated Problem Status');
                        });
                    });

                });

                $interval(function () {
                    $scope.refresh_problem_activity();
                }, 10000);

            }

            /**
             * Callback after todo have success change it status from accomplished <-> pending
             * @param list
             * @param todo
             */
            function changeTodoList(list, todo) {
                patientService.toggleTodoStatus(todo);
            }

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

            function convertDateTimeBack(dateTime) {
                if (dateTime) {
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

                return timeline_problems;
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
                var event = {};
                event['event_id'] = new Date().getTime();
                event['startTime'] = moment().format('DD/MM/YYYY HH:mm:ss');
                event['state'] = getTimelineWidgetState(problem);

                return event;
            }

            function changeView(viewName) {
                $scope.viewMode = viewName;
                angular.forEach($scope.datas, function (data, key) {

                    // Default graph type
                    if (data.graph == null || data.graph === undefined)
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

            function timelineSave(newData) {
                var form = {};

                form.patient_id = $scope.patient_id;
                form.timeline_data = newData;
                $scope.problem.start_date = convertDateTimeBack(newData.problems[0].events[0].startTime);

                problemService.updateByPTW(form).then(function (data) {
                    toaster.pop('success', 'Done', 'Updated Problem');
                });
            }

            function delete_problem() {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a problem is forever. There is no undo."
                }).then(function (result) {
                    var form = {};
                    form.problem_id = $scope.problem_id;
                    form.patient_id = $scope.patient_id;
                    problemService.deleteProblem(form).then(function (data) {
                        toaster.pop('success', 'Done', 'Deleted problem successfully');
                        $location.url('/');
                    });
                }, function () {
                    return false;
                });
            }

            function problem_name_changed(problem_term) {

                $scope.unset_new_problem();
                if (problem_term.length > 2) {
                    patientService.listTerms(problem_term).then(function (data) {
                        $scope.problem_terms = data;
                    });
                } else {
                    $scope.problem_terms = [];
                }
            }

            function set_new_problem(problem) {

                $scope.new_problem.set = true;
                $scope.new_problem.active = problem.active;
                $scope.new_problem.term = problem.term;
                $scope.new_problem.code = problem.code;


            }

            function unset_new_problem() {

                $scope.new_problem.set = false;

            }

            function change_problem_name() {

                var c = confirm("Are you sure?");

                if (c == false) {
                    return false;
                }

                var form = {};
                form.term = $scope.new_problem.term;
                form.code = $scope.new_problem.code;
                form.problem_id = $scope.problem_id;

                problemService.changeProblemName(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Problem name changed successfully');
                        $scope.problem = data['problem'];
                        $scope.problem_term = '';
                        $scope.unset_new_problem();
                        /* Not-angular-way */
                        $('#problemTermInput').focus();
                        $scope.set_authentication_false();

                    } else if (data['success'] == false) {
                        alert(data['msg']);
                    } else {
                        alert("Something went wrong");
                    }


                });


            }

            function change_new_problem_name(problem_term) {
                if (problem_term == '' || problem_term == undefined) {
                    return false;
                }

                var c = confirm("Are you sure?");

                if (c == false) {
                    return false;
                }


                var form = {};
                form.term = problem_term;
                form.problem_id = $scope.problem_id;

                problemService.changeProblemName(form).then(function (data) {

                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Problem name changed successfully');
                        $scope.problem = data['problem'];
                        $scope.problem_term = '';
                        $scope.unset_new_problem();
                        /* Not-angular-way */
                        $('#problemTermInput').focus();
                        $scope.set_authentication_false();
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', data['msg']);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong');
                    }
                });
            }

            function open_change_problem_label() {
                $scope.change_problem_label = true;
            }

            function close_change_problem_label() {
                $scope.change_problem_label = false;
            }

            function open_create_problem_label() {
                $scope.create_problem_label = true;
            }

            function close_create_problem_label() {
                $scope.create_problem_label = false;
            }

            function selectProblemLabelComponent(component) {
                $scope.problem_label_component.css_class = component.css_class;
            }

            function saveCreateProblemLabel(problem) {
                if ($scope.problem_label_component.css_class != null) {
                    problemService.saveCreateLabel($scope.problem_id, $scope.problem_label_component).then(function (data) {
                        if (data['success'] == true) {
                            if (data['new_status'] == true) {
                                $scope.problem_labels.push(data['new_label']);
                            }
                            if (data['status'] == true) {
                                problem.labels.push(data['label']);
                                toaster.pop('success', "Done", "Added Problem label!");
                            }
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                $scope.create_problem_label = false;
            }

            function editProblemLabel(label) {
                label.edit_label = (label.edit_label != true) ? true : false;
            }

            function selectEditProblemLabelComponent(label, component) {
                label.css_class = component.css_class;
            }

            function saveEditProblemLabel(label) {
                if (label.css_class != null) {
                    problemService.saveEditLabel(label, $scope.patient_id, $scope.user_id).then(function (data) {
                        if (data['success'] == true) {
                            label.css_class = data['label']['css_class'];
                            if (data['status'] == true) {
                                angular.forEach($scope.problem.labels, function (value, key) {
                                    if (value.id == label.id) {
                                        value.css_class = label.css_class;
                                    }
                                });
                                toaster.pop('success', "Done", "Changed label!");
                            }
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }
                label.edit_label = false;
            }

            function changeProblemLabel(problem, label) {

                var is_existed = false;
                var existed_key;
                var existed_id;

                angular.forEach(problem.labels, function (value, key) {
                    if (value.name == label.name) {
                        is_existed = true;
                        existed_key = key;
                        existed_id = value.id;
                    }
                });
                if (!is_existed) {
                    problem.labels.push(label);
                    problemService.addProblemLabel(label.id, problem.id).then(function (data) {
                        if (data['success'] == true) {
                            toaster.pop('success', "Done", "Added Problem label!");
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                } else {
                    problem.labels.splice(existed_key, 1);
                    problemService.removeProblemLabel(existed_id, problem.id).then(function (data) {
                        if (data['success'] == true) {
                            toaster.pop('success', "Done", "Removed Problem label!");
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }

            }

            function deleteEditProblemLabel(label) {
                prompt({
                    "title": "Are you sure?",
                    "message": "Deleting a label is forever. There is no undo."
                }).then(function (result) {
                    problemService.deleteLabel(label).then(function (data) {
                        var index = $scope.problem_labels.indexOf(label);
                        $scope.problem_labels.splice(index, 1);

                        var index2;
                        angular.forEach($scope.problem.labels, function (value, key) {
                            if (value.id == label.id) {
                                index2 = key;
                            }
                        });
                        if (index2 != undefined)
                            $scope.problem.labels.splice(index2, 1);

                        toaster.pop('success', 'Done', 'Deleted label successfully');
                    });
                }, function () {
                    return false;
                });
            }

            function openCreateLabelProblemsList() {
                $scope.create_label_problems_list = true;
            }

            function close_create_label_problems_list() {
                $scope.create_label_problems_list = false;
            }

            function add_new_list_label(new_list, label) {
                var index = new_list.labels.indexOf(label);
                if (index > -1)
                    new_list.labels.splice(index, 1);
                else
                    new_list.labels.push(label);
            }

            function add_problem_list(form) {

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
            }

            function set_authentication_false() {
                if ($scope.active_user.role != "physician" && $scope.active_user.role != "admin")
                    $scope.problem.authenticated = false;
            }

            function update_start_date() {

                var form = {};

                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.problem.id;
                form.start_date = $scope.problem.start_date;

                if (!moment(form.start_date, "MM/DD/YYYY", true).isValid()) {
                    toaster.pop('error', 'Error', 'Please enter a valid date!');
                    return false;
                }

                problemService.updateStartDate(form).then(function (data) {
                    toaster.pop('success', 'Done', 'Updated Start Date');
                    $scope.set_authentication_false();
                    $scope.timeline.problems[0].events[0].startTime = convertDateTime($scope.problem);
                    $scope.timeline_changed.push({changing: new Date().getTime()});
                });
            }

            function add_wiki_note(form) {
                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.problem.id;

                problemService.addWikiNote(form).then(function (data) {

                    if (data.success) {
                        toaster.pop('success', 'Done', 'Added Wiki Note');

                        var note = data['note'];
                        if ($scope.active_user.role == 'patient') {
                            $scope.patient_wiki_notes.unshift(note);
                        } else if ($scope.active_user.role == 'physician') {
                            $scope.show_physician_notes = true;
                            $scope.physician_wiki_notes.unshift(note);
                        } else {
                            $scope.show_other_notes = true;
                            $scope.other_wiki_notes.unshift(note);
                        }
                        form.note = '';

                        $scope.set_authentication_false();

                        // https://trello.com/c/ZFlgZLOz. Move cursor to todo input text field
                        $('#todoNameInput').focus();

                        // Push newly added todo to active todo list
                        if (data.hasOwnProperty('todo')) {
                            patientService.addTodoCallback(data.todo);
                        }
                    } else {
                        toaster.pop('error', 'Warning', 'Action Failed');
                    }

                }, function (error) {
                    toaster.pop('error', 'Warning', 'Something went wrong!');

                });

            }

            function add_history_note(form) {
                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.problem.id;

                problemService.addHistoryNote(form).then(function (data) {

                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Added History Note');

                        $scope.history_note = data['note'];
                        $scope.set_authentication_false();

                        if (data.hasOwnProperty('todo')) {
                            patientService.addTodoCallback(data.todo);
                        }

                    } else {
                        toaster.pop('error', 'Warning', 'Action Failed');
                    }

                }, (e) => {
                    toaster.pop('error', 'Warning', 'Something went wrong!');

                });

            }

            function add_goal(form) {

                if (form == undefined) {
                    return false;
                }

                if (form.name.trim().length < 1) {
                    return false;
                }

                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.problem.id;
                problemService.addGoal(form).then(function (data) {

                    form.name = '';
                    $scope.problem_goals.push(data['goal']);
                    toaster.pop('success', 'Done', 'Added Goal!');
                    $scope.set_authentication_false();
                    /* Not-angular-way */
                    $('#goalNameInput').focus();
                });
            }

            function addTodo(form) {
                if (_.isUndefined(form) || form.name.trim().length < 1) {
                    return false;
                }
                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.problem.id;

                if ($scope.bleeding_risk) {
                    ngDialog.open({
                        template: 'bleedingRiskDialog',
                        showClose: false
                    }).closePromise.then(askDueDate);
                } else {
                    askDueDate();
                }

                function askDueDate() {
                    var acceptedFormat = ['MM/DD/YYYY', "M/D/YYYY", "MM/YYYY", "M/YYYY", "MM/DD/YY", "M/D/YY", "MM/YY", "M/YY"];
                    ngDialog.open({
                        template: 'askDueDateDialog',
                        showClose: false,
                        controller: function () {
                            var vm = this;
                            vm.dueDate = "";
                            vm.dueDateIsValid = dueDateIsValid;

                            function dueDateIsValid() {
                                let isValid = moment(vm.dueDate, acceptedFormat, true).isValid();
                                if (!isValid)
                                    toaster.pop('error', 'Error', 'Please enter a valid date!');
                                return isValid;
                            }
                        },
                        controllerAs: 'vm'
                    }).closePromise.then(function (data) {
                        if (!_.isUndefined(data.value) && '$escape' !== data.value && '$document' !== data.value)
                            form.due_date = moment(data.value, acceptedFormat).toString();
                        // Is this should be called from problem service or todo service or shared/common service
                        patientService.addProblemTodo(form).then(postAddTodo);
                        // problemService.addTodo(form).then(postAddTodo);
                    });
                }

                // Going to
                function postAddTodo(response) {
                    if (response.success) {
                        toaster.pop('success', 'Done', 'Added Todo!');

                        var addedTodo = response.todo;
                        form.name = '';
                        // $scope.pending_todos.push(addedTodo);
                        $scope.set_authentication_false();

                        // Showing tag member dialog
                        ngDialog.open({
                            template: 'postAddTodoDialog',
                            showClose: false,
                            scope: $scope,
                            controller: function () {
                                var vm = this;
                                vm.taggedMembers = [];

                                vm.memberSearch = "";
                                vm.memberList = $scope.members;

                                vm.toggleTaggedMember = toggleTaggedMember;
                                vm.memberFilter = memberFilter;

                                function memberFilter(item) {
                                    return item.user.first_name.indexOf(vm.memberSearch) !== -1 || item.user.last_name.indexOf(vm.memberSearch) !== -1;
                                }

                                function toggleTaggedMember(member, event) {
                                    let idx = vm.taggedMembers.indexOf(member.id);
                                    idx === -1 ? vm.taggedMembers.push(member.id) : vm.taggedMembers.splice(idx, 1);

                                    // Refocus to form search to enable handle enter press key
                                    $(event.currentTarget.parentElement).find("input").focus();
                                }

                            },
                            controllerAs: 'vm'
                        }).closePromise.then(data => {
                            if (!_.isUndefined(data.value) && "$escape" !== data.value && "$document" !== data.value) {
                                // Added tagged member to previous added todo
                                _.each(data.value, (memberID) => {
                                    let member = _.find($scope.members, (member) => member.id === memberID);
                                    addedTodo.members.push(member.user);
                                    todoService.addTodoMember(addedTodo, member).then(() => {
                                        toaster.pop('success', 'Done', `Add ${member.user.first_name} ${member.user.last_name} succeeded!`);
                                    }, () => {
                                        toaster.pop('error', 'Error', `Add ${member.user.first_name} ${member.user.last_name}  failed!`);
                                    });
                                });
                            }

                            // Comeback to normal state
                            $('#todoNameInput').val("");
                            $('#todoNameInput').focus();
                        });
                    } else {
                        toaster.pop('error', 'Error', "Failed to add todo");
                    }
                }
            }


            function open_image_upload_box(files) {
                var url = '/p/problem/' + $scope.problem_id + '/upload_image';
                $scope.files = files;
                if (files && files.length) {
                    Upload.upload({
                        url: url,
                        data: {
                            files: files
                        },
                        headers: {'Content-Type': undefined}
                    }).then(uploadSuccess);
                }

                function uploadSuccess(response) {
                    toaster.pop('success', 'Done', 'Image uploaded');
                    $scope.problem_images = $scope.problem_images.concat(response.data.images);
                }
            }

            function open_image_box(image) {

                ngDialog.open({
                    template: 'imageBoxDialog',
                    className: 'ngdialog-theme-default large-modal',
                    scope: $scope,
                    cache: false,
                    controller: ['$scope',
                        function ($scope) {

                            $scope.image = image;

                            $scope.set_authentication_false();
                        }]
                });

            }

            function delete_problem_image(image) {

                var c = confirm("Are you sure ?");

                if (c == false) {
                    return false;
                }

                var form = {};
                form.patient_id = $scope.patient_id;
                form.problem_id = $scope.problem.id;
                form.image_id = image.id;

                problemService.deleteProblemImage(form).then(function (data) {

                    var image_index = $scope.problem_images.indexOf(image);

                    $scope.problem_images.splice(image_index, 1);
                    toaster.pop('success', 'Done', 'Deleted image!');
                    $scope.set_authentication_false();
                });
            }

            function id_exists(id, item_list) {

                var found = false;

                angular.forEach(item_list, function (value) {

                    if (value == id) {
                        found = true;
                    }

                });

                return found;

            }

            function change_effecting_problem(source, problem) {

                var effecting = source.effecting;

                var form = {};
                form.source_id = source.id;
                form.target_id = problem.id;
                form.relationship = effecting;
                problemService.relateProblem(form).then(function (data) {
                    toaster.pop('success', "Done", "Updated relationship !");
                    $scope.set_authentication_false();
                });

            }

            function change_effected_problem(problem, target) {


                var effected = target.effected;

                var form = {};
                form.source_id = problem.id;
                form.target_id = target.id;
                form.relationship = effected;

                problemService.relateProblem(form).then(function (data) {
                    toaster.pop('success', "Done", "Updated relationship !");
                    $scope.set_authentication_false();

                });

            }

            function permitted(permissions) {

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

            }

            function toggle_other_notes() {

                if ($scope.show_other_notes == true) {
                    $scope.show_other_notes = false;
                } else {
                    $scope.show_other_notes = true;
                }
            }

            function toggle_physician_notes() {

                if ($scope.show_physician_notes == true) {
                    $scope.show_physician_notes = false;
                } else {
                    $scope.show_physician_notes = true;
                }
            }

            function refresh_problem_activity() {
                problemService.getProblemActivity($scope.problem_id, $scope.current_activity).then(function (data) {
                    if (data['activities'].length) {
                        for (var i = data['activities'].length - 1; i >= 0; i--) {
                            $scope.activities.unshift(data['activities'][i]);
                        }
                        $scope.current_activity = data['activities'][0].id;
                    }
                })
            }

            function toggle_accomplished_todos() {

                // var flag = $scope.show_accomplished_todos;
                //
                // if (flag == true) {
                //     flag = false;
                // } else {
                //     flag = true;
                // }
                //
                // $scope.show_accomplished_todos = flag;
                // $scope.todos_ready = false;

                $scope.show_accomplished_todos = !$scope.show_accomplished_todos;
                if (!$scope.accomplishedTodoLoaded) {
                    problemService.getRelatedTodos($scope.problem_id, true, $scope.accomplishedTodoPage, true)
                        .then((resp) => {
                            if (resp.success) {
                                // if loading from remote then replace it cuz it fresh & trusted data source
                                $scope.accomplished_todos = resp.data;
                                $scope.accomplishedTodoLoaded = true;
                            }
                        });
                }
            }

            function toggle_accomplished_goals() {

                var flag = $scope.show_accomplished_goals;

                if (flag == true) {
                    flag = false;
                } else {
                    flag = true;
                }

                $scope.show_accomplished_goals = flag;
            }

            function checkSharedProblem(problem, sharing_patients) {
                if ($scope.active_user) {

                    if ($scope.patient_id == $scope.user_id || $scope.active_user.role != 'patient') {
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
                }
            }

            function isInArray(array, item) {
                var is_existed = false;
                angular.forEach(array, function (value, key2) {
                    if (value == item) {
                        is_existed = true;
                    }
                });
                return is_existed;
            }


            function open_data(data) {
                $location.path('/data/' + data.id);
            }

            function open_change_data() {
                $scope.change_pinned_data = true;
            }

            function close_change_data() {
                $scope.change_pinned_data = false;
            }

            function data_pin_to_problem(data_id, problem_id) {
                var form = {};
                form.data_id = data_id;
                form.problem_id = problem_id;

                dataService.dataPinToProblem($scope.patient_id, form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Pinned data!');
                        if (data.inr)
                            $scope.inrs.push(data.inr);
                        else if (data.remove_inr)
                            $scope.inrs = [];

                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            }

            function open_medication(medication) {
                $location.url('/medication/' + medication.id);
            }

            function open_change_medication() {
                $scope.change_pinned_medication = true;
            }

            function close_change_medication() {
                $scope.change_pinned_medication = false;
            }

            function medication_pin_to_problem(medication, problem_id) {
                var form = {};
                form.medication_id = medication.id;
                form.problem_id = problem_id;

                medicationService.medicationPinToProblem($scope.patient_id, form).then(function (data) {
                    if (data['success'] == true) {
                        var is_pin = false;
                        angular.forEach($scope.medications, function (medication, key) {
                            if (medication.pin)
                                is_pin = true;
                            $scope.hasPinnedMedication = is_pin;
                        });
                        toaster.pop('success', 'Done', 'Pinned problem!');
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            }

            function goToMedicationTab() {
                CollapseService.ChangeHomepageTab('medication');
                $location.path('/');
            }

            function addMedication(medication) {
                medication.patient_id = $scope.patient_id;

                medicationService.addMedication(medication).then(addMedicationProblemSuccessCallback);

                function addMedicationProblemSuccessCallback(data) {
                    if (data.success) {
                        $timeout(() => {
                            $("#addMedicationBtn").click();
                        }, 100);


                        // Medication pin/unpin pen action
                        data.medication.pin = true;
                        $scope.medications.push(data.medication);

                        // Medication widget
                        $scope.medication_pins.push(data.medication);

                        // Auto pin
                        $scope.medication_pin_to_problem(data.medication, $scope.problem_id);
                    } else {
                        toaster.pop('error', 'Error', 'Failed to add medication. Please try again!');
                    }
                }
            }

            function widgetTodoAdded(todo) {
                $scope.pending_todos.push(todo);
            }

            function widgetTodoStatusChanged(todo) {
                $scope.accomplished_todos.push(todo);

                // Problem page overall pending todo list
                var idx = -1;
                _.each($scope.pending_todos, (element, index, list) => {
                    if (element.id === todo.id) {
                        idx = index;
                    }
                });
                if (idx !== -1) {
                    $scope.pending_todos.splice(idx, 1);
                }
            }

            function loadMoreTodo() {
                if (!$scope.todoIsLoading) {
                    $scope.todoIsLoading = true;

                    patientService.loadMoreTodo($scope.patient_id);
                }
            }
        });
    /* End of controller */
})();
