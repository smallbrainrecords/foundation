/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
(function () {
    'use strict';
    angular.module('ManagerApp')
        .controller('HomeCtrl', HomeCtrl);
    HomeCtrl.$inject = ['$scope', 'patientService', 'problemService', 'encounterService',
        'ngDialog', 'sharedService', 'dataService', 'toaster', '$location', 'todoService',
        'prompt', '$timeout', 'CollapseService', '$filter', '$window'];

    /**
     *
     * @param $scope
     * @param patientService
     * @param problemService
     * @param encounterService
     * @param ngDialog
     * @param sharedService
     * @param dataService
     * @param toaster
     * @param $location
     * @param todoService
     * @param prompt
     * @param $timeout
     * @param CollapseService
     * @param $filter
     * @param $window
     * @constructor
     */
    function HomeCtrl($scope, patientService, problemService, encounterService, ngDialog, sharedService, dataService,
                      toaster, $location, todoService, prompt, $timeout, CollapseService, $filter, $window) {
        console.log("controller: HomeCtrl");
        $scope.patientService = patientService;
        $scope.btnBDFISubmitted = false;
        $scope.collapse = CollapseService;
        $scope.datas = [];
        $scope.favorites_collapse = false;
        $scope.is_home = true;
        $scope.most_recent_encounter_documents = [];
        $scope.my_story_tabs = [];
        $scope.myStoryTabTextComponentArray = [];
        $scope.new_data_type = {};
        $scope.new_list = {};
        $scope.new_list.labels = [];
        $scope.new_problem = {set: false};
        $scope.new_tab = {};
        $scope.new_tab.all_patients = true;
        $scope.new_tab.private = true;
        $scope.new_text = {};
        $scope.new_text.all_patients = true;
        $scope.new_text.private = true;
        $scope.problem_lists = [];
        $scope.problem_term = '';
        $scope.problem_terms = [];
        $scope.selected_tab = null;
        $scope.show_accomplished_todos = false;
        $scope.show_add_my_story_tab = false;
        $scope.show_add_my_story_text = false;
        $scope.show_add_new_data_type = false;
        $scope.show_edit_my_story_tab = false;
        $scope.show_previous_entries = false;
        $scope.graphicFrameIsCollapsed = false;
        $scope.viewMode = 'Year';
        $scope.sortingLogProblem = [];
        $scope.sortedProblem = false;
        $scope.draggedProblem = false;
        $scope.todoIsLoading = false;
        $scope.narrativeHistories = [];
        $scope.showNarrative = false;
        $scope.narratives = {
            latest: {},
            total: 6
        };

        $scope.add_bfdi_value = addBfdiValue;
        $scope.add_goal = addGoal;
        $scope.add_my_story_tab = addMyStoryTab;
        $scope.add_my_story_text = addMyStoryText;
        $scope.add_new_common_problem = addNewCommonProblem;
        $scope.add_new_data_type = addNewDataType;
        $scope.add_new_list_label = addNewListLabel;
        $scope.add_new_problem = addNewProblem;
        $scope.add_problem = addProblem;
        $scope.add_problem_list = addProblemList;
        $scope.add_todo = addTodo;
        $scope.change_component_text = changeComponentText;
        $scope.change_homepage_tab = changeHomepageTab;
        $scope.check_has_data_loinc_code = checkHasDataLoincCode;
        $scope.check_problem_list_authenticated = checkProblemListAuthenticated;
        $scope.check_problem_list_controlled = checkProblemListControlled;
        $scope.checkSharedMyStory = checkSharedMyStory;
        $scope.checkSharedProblem = checkSharedProblem;
        $scope.delete_list = deleteList;
        $scope.delete_my_story_tab = deleteMyStoryTab;
        $scope.delete_my_story_text = deleteMyStoryText;
        $scope.edit_my_story_tab = editMyStoryTab;
        $scope.fetchTimeLineProblem = fetchTimeLineProblem;
        $scope.fileUploadSuccess = fileUploadSuccess;
        $scope.inArray = inArray;
        $scope.isInArray = isInArray;
        $scope.nameFavoriteEvent = nameFavoriteEvent;
        $scope.nurseSubmitBDFI = nurseSubmitBDFI;
        $scope.open_problem = openProblem;
        $scope.permitted = permitted;
        $scope.problemTermChanged = problemTermChanged;
        $scope.rename_list = renameList;
        $scope.save_my_story_tab = saveMyStoryTab;
        $scope.save_my_story_text = saveMyStoryText;
        $scope.see_previous_entries = seePreviousEntries;
        $scope.set_collapse = setCollapse;
        $scope.set_new_problem = setNewProblem;
        $scope.timelineSave = timelineSave;
        $scope.toggle_accomplished_todos = toggleAccomplishedTodos;
        $scope.toggle_add_my_story_tab = toggleAddMyStoryTab;
        $scope.toggle_add_my_story_text = toggleAddMyStoryText;
        $scope.toggle_add_new_data_type = toggleAddNewDataType;
        $scope.unmarkFavoriteEvent = unmarkFavoriteEvent;
        $scope.unset_new_problem = unsetNewProblem;
        $scope.update_patient_note = updatePatientNote;
        $scope.update_problem_list_note = updateProblemListNote;
        $scope.updateStatusCallback = changeTodoList;
        $scope.updateSummary = updateSummary;
        $scope.view_my_story_tab = viewMyStoryTab;
        $scope.addProblemIsSelected = addProblemIsSelected;
        $scope.bdfiValueIsChanged = bdfiValueIsChanged;
        $scope.loadMoreTodo = loadMoreTodo;
        $scope.loadMore = loadMoreNarrative;
        $scope.addNarrative = addNarrative;

        init();

        function init() {
            $scope.pending_todos = patientService.pendingTodo;
            $scope.accomplished_todos = patientService.accomplishedTodo;

            // Each time reload the controller need to reset loading flag
            patientService.pendingTodoLoaded = false;
            patientService.fetchPatientInfo($scope.patient_id).then(function (response) {
                let data = response.data;
                $scope.acutes = data['acutes_list'];
                $scope.chronics = data['chronics_list'];

                $scope.problems = data['problems'];
                $scope.inactive_problems = data['inactive_problems'];

                $scope.goals = data['goals'];
                $scope.completed_goals = data['completed_goals'];

                $scope.encounters = data['encounters'];
                $scope.favorites = data['favorites'];


                $scope.shared_patients = data['shared_patients'];
                $scope.sharing_patients = data['sharing_patients'];

                var tmpListProblem = $scope.problems;
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
                            patientService.updateProblemOrder(form).then(function (response) {
                                let data = response.data;
                                toaster.pop('success', 'Done', 'Updated Problem Order');
                            });
                        }
                        $scope.sortedProblem = false;
                        $timeout(function () {
                            $scope.draggedProblem = false;
                        }, 100);
                    }
                };
            });

            problemService.fetchLabeledProblemList($scope.patient_id, $scope.user_id).then(function (response) {
                let data = response.data;
                $scope.problem_lists = data['problem_lists'];
                $scope.problems_ready = true;
            });

            // Documentation
            patientService.getDocuments($scope.patient_id).then(function (response) {
                let data = response.data;
                if (data['success'] === true) {
                    $scope.documents = data['info'];
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });

            patientService.fetchNarrative($scope.patient_id).then(response => {
                $scope.narratives = response.data;
            });

            // TODO: This should be set to global usage
            todoService.fetchTodoMembers($scope.patient_id).then(function (response) {
                let data = response.data;
                $scope.members = data['members'];
            });

            // TODO: This should be set to global usage
            todoService.fetchLabels($scope.patient_id).then(function (response) {
                let data = response.data;
                $scope.labels = data['labels'];
            });


            // TODO: Low priority load
            patientService.getMyStory($scope.patient_id).then(function (response) {
                let data = response.data;
                if (data['success']) {
                    $scope.my_story_tabs = data['info'];
                    $scope.selected_tab = $scope.my_story_tabs[0];
                    $scope.myStoryTabTextComponentArray = _.flatten(_.pluck($scope.my_story_tabs, 'my_story_tab_components'));
                }
            });

            // TODO: Low priority load
            patientService.getDatas($scope.patient_id).then(function (response) {
                let data = response.data;
                if (data['success']) {
                    $scope.datas = data['info'];
                    // TODO: DRY
                    angular.forEach($scope.datas, function (data, key) {
                        // Default graph type
                        if (data.graph == null)
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
                        if ("blood pressure" === data.name) {
                            $("#vitals_blood_pressure").html(`<a title="Blood Pressure" href="#/data/${data.id}">BP: ${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue}</a>`);
                        }

                        if ("body temperature" === data.name) {
                            $("#vitals_body_temperature").html(`<a title="Body Temperature" href="#/data/${data.id}">T: ${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue}</a>`);
                        }
                        if ("weight" === data.name) {
                            $("#vitals_weight").html(`<a title="Weight" href="#/data/${data.id}">W: ${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue}</a>`);
                        }

                        if ("heart rate" === data.name) {
                            $("#vitals_heart_rate ").html(`<a title="Heart Rate" href="#/data/${data.id}">P: ${_.isEmpty(data.mostRecentValue) ? 'N/A' : data.mostRecentValue}</a>`);
                        }
                    });
                    if ($scope.active_user) {
                        if ($scope.active_user.role === 'patient') {
                            $scope.mostCommonData = dataService.generateMostCommonData($scope.datas);
                        }
                        if ($scope.active_user.role === 'nurse') {
                            console.log('aaaa');
                            $scope.mostCommonData = [];
                            // Related to https://trello.com/c/0aJybixw
                            // Pick  most common data with sorted order weight data first
                            let weight = _.findWhere($scope.datas, {'name': 'weight'});
                            weight.ph = 'W';
                            $scope.mostCommonData.push(weight);

                            let height = _.findWhere($scope.datas, {'name': 'height'});
                            height.ph = 'H';
                            $scope.mostCommonData.push(height);

                            let blood_pressure = _.findWhere($scope.datas, {'name': 'blood pressure'});
                            blood_pressure.ph = 'BP';
                            $scope.mostCommonData.push(blood_pressure);

                            let body_temperature = _.findWhere($scope.datas, {'name': 'body temperature'});
                            body_temperature.ph = 'T';
                            $scope.mostCommonData.push(body_temperature);


                            let heart_rate = _.findWhere($scope.datas, {'name': 'heart rate'});
                            heart_rate.ph = 'Pulse';
                            $scope.mostCommonData.push(heart_rate);


                            let respiratory_rate = _.findWhere($scope.datas, {'name': 'respiratory rate'});
                            respiratory_rate.ph = 'RR';
                            $scope.mostCommonData.push(respiratory_rate);
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
                                patientService.updateDataOrder(form).then(function (response) {
                                    let data = response.data;
                                    toaster.pop('success', 'Done', 'Updated Data Order');
                                });
                            }
                            $scope.sortedData = false;
                            $timeout(function () {
                                $scope.draggedData = false;
                            }, 100);
                        }
                    };

                    $scope.open_data = function open_data(data) {
                        if (!$scope.draggedData) {
                            var form = {};
                            form.patient_id = $scope.patient_id;
                            form.observation_id = data.id;
                            patientService.trackDataClickEvent(form).then(function (response) {
                                let data = response.data;
                            });
                            $location.path('/data/' + data.id);
                        }
                    };
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });

            // TODO: Low priority load
            patientService.getMedications($scope.patient_id).then(function (response) {
                let data = response.data;
                if (data['success']) {
                    $scope.medications = data['info'];
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });

            $scope.$watch("viewMode", function (newVal, oldVal) {
                if (newVal !== oldVal) {
                    angular.forEach($scope.datas, function (data, key) {
                        // Default graph type
                        if (data.graph === null || data.graph === undefined)
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
                if ($scope.files !== undefined)
                    sharedService.uploadDocument($scope.files, $scope.user_id, $scope.patient_id, $scope.fileUploadSuccess);
            });

            $scope.$watch('collapse.show_homepage_tab', function (newVal, oldVal) {
                if ("medication" === newVal && encounterService.activeEncounter.is_active) {
                    var form = {
                        'event': "Medication list was accessed"
                    };
                    encounterService.addEncounterEvent(encounterService.activeEncounter.id, form);
                }
            });

            $scope.$on('portrait_image_updated', function (event, args) {
                $scope.patient_info = args.data;
            });

            $scope.$on('tabPressed', function (event, args) {
                if ('mystory' === $scope.collapse.show_homepage_tab) {
                    // Finding current DOM element which is focused
                    var activeElement = document.activeElement;
                    if (activeElement && _.contains(activeElement.classList, 'tab-components')) {
                        var nextFocusedComponentId = parseInt(activeElement.id) + 1;
                        var currentComponent = $scope.myStoryTabTextComponentArray[activeElement.id - 1];
                        var nextComponent = $scope.myStoryTabTextComponentArray[activeElement.id];
                        if (nextComponent.tab !== currentComponent.tab) {
                            var nexTabToBeActivated = _.find($scope.my_story_tabs, function (tab) {
                                return nextComponent.tab === tab.id;
                            });
                            $scope.view_my_story_tab(nexTabToBeActivated)
                        }
                    } else {
                        // Finding next tab which have at least one component after the selected tabs which does not have any text component
                        while ($scope.selected_tab.my_story_tab_components.length === 0) {
                            $scope.selected_tab = _.find($scope.my_story_tabs, function (tab) {
                                return tab.my_story_tab_components.length > 0 && tab.id >= $scope.selected_tab.id
                            });
                        }
                        $scope.view_my_story_tab($scope.selected_tab);

                        // Finding first component of actived tab
                        var component = _.find($scope.myStoryTabTextComponentArray, function (component) {
                            return component.tab === $scope.selected_tab.id;
                        });
                        var nextFocusedComponentId = $scope.myStoryTabTextComponentArray.indexOf(component) + 1;
                    }

                    setTimeout(function () {
                        $('.tab-components#' + nextFocusedComponentId).focus();
                    }, 0);
                }
            });

            // Load graphics frame only when it is opened
        }

        $scope.$on('todoListUpdated', function (event, args) {
            $scope.pending_todos = patientService.pendingTodo;
            $scope.todoIsLoading = false;
        });

        function loadMoreTodo(accomplished) {
            // Only load more if there is no request in progress OR all data is loaded
            if (!$scope.todoIsLoading) {
                // patientService.pendingTodoLoaded -> data/service flag
                $scope.todoIsLoading = true;

                patientService.progressiveTodoLoading($scope.patient_id);
            }
        }


        function problemTermChanged(term) {
            $scope.unset_new_problem();
            if (term.length > 2) {
                patientService.listTerms(term).then(function (response) {
                    let data = response.data;
                    $scope.problem_terms = data;
                });
            } else {
                $scope.problem_terms = [];
            }
        }

        function timelineSave(newData) {
            var form = {};
            form.patient_id = $scope.patient_id;
            form.timeline_data = newData;
            problemService.updateByPTW(form).then(function (response) {
                let data = response.data;
                toaster.pop('success', 'Done', 'Updated Problems');
            });
        }

        function fetchTimeLineProblem(data) {
            patientService.fetchTimeLineProblem($scope.patient_id).then(function (response) {
                let data2 = response.data;
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
        }

        /**
         * Load accomplished todo
         */
        function toggleAccomplishedTodos() {
            $scope.show_accomplished_todos = !$scope.show_accomplished_todos;
            // $scope.todos_ready = false;
            if (!$scope.accomplishedTodoLoaded) {
                patientService.getToDo($scope.patient_id, true, true, $scope.accomplishedTodoPage).then((response) => {
                    let resp = response.data;
                    if (resp.success) {
                        // if loading from remote then replace it cuz it fresh & trusted data source
                        $scope.accomplished_todos = resp.data;
                        $scope.accomplishedTodoLoaded = true;
                    }
                });
            }
        }

        function addGoal(form) {
            form.patient_id = $scope.patient_id;
            patientService.addGoal(form).then(function (response) {
                let data = response.data;
                var new_goal = data['goal'];
                $scope.goals.push(new_goal);
                toaster.pop('success', "Done", "New goal created successfully!");
                console.log('pop');
            });
        }

        function addTodo(form) {
            if (form === undefined || form.name.trim().length < 1) {
                return false;
            }
            form.patient_id = $scope.patient_id;
            if ($scope.bleeding_risk) {
                ngDialog.open({
                    template: 'bleedingRiskDialog',
                    showClose: false,
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
                }).closePromise.then(function (response) {
                    let data = response;
                    if (!_.isUndefined(data.value) && '$escape' !== data.value && '$document' !== data.value)
                        form.due_date = moment(data.value, acceptedFormat).toString();
                    sharedService.addToDo(form).then(postAddTodo);
                });
            }

            // Going to
            function postAddTodo(response) {
                if (response.success) {
                    toaster.pop('success', 'Done', 'Added Todo!');

                    let addedTodo = response.todo;
                    $scope.pending_todos.push(addedTodo);
                    // $scope.problem_todos.push(addedTodo);
                    $scope.new_todo = {};

                    // Showing tag member dialog
                    ngDialog.open({
                        template: 'postAddTodoDialog',
                        showClose: false,
                        scope: $scope,
                        controller: function () {
                            let vm = this;
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

        function setNewProblem(problem) {
            $scope.new_problem.set = true;
            $scope.new_problem.active = problem.active;
            $scope.new_problem.term = problem.term;
            $scope.new_problem.code = problem.code;
        }

        function unsetNewProblem() {
            $scope.new_problem.set = false;
        }

        function addProblem() {
            var c = confirm("Are you sure?");
            if (c === false) {
                return false;
            }
            var form = {};
            form.patient_id = $scope.patient_id;
            form.term = $scope.new_problem.term;
            form.code = $scope.new_problem.code;
            form.active = $scope.new_problem.active;
            patientService.addProblem(form).then(function (response) {
                let data = response.data;
                if (data['success'] === true) {
                    toaster.pop('success', 'Done', 'New Problem added successfully');
                    $scope.problems.push(data['problem']);
                    $scope.problem_term = '';
                    $scope.unset_new_problem();
                    /* Not-angular-way */
                    $('#problemTermInput').focus();

                    //
                    $scope.open_problem(data['problem']);
                } else if (data['success'] === false) {
                    alert(data['msg']);
                } else {
                    alert("Something went wrong");
                }
            });
        }

        function addNewProblem(problem_term) {
            if (problem_term === '' || problem_term === undefined) {
                return false;
            }
            var c = confirm("Are you sure?");
            if (c === false) {
                return false;
            }
            var form = {};
            form.patient_id = $scope.patient_id;
            form.term = problem_term;
            patientService.addProblem(form).then(function (response) {
                let data = response.data;
                if (data['success'] === true) {
                    toaster.pop('success', 'Done', 'New Problem added successfully');
                    $scope.problems.push(data['problem']);
                    $scope.problem_term = '';
                    $scope.unset_new_problem();
                    /* Not-angular-way */
                    $('#problemTermInput').focus();

                    $scope.open_problem(data['problem']);

                } else if (data['success'] === false) {
                    toaster.pop('error', 'Error', data['msg']);
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong');
                }
            });
        }

        function addNewCommonProblem(problem, type) {
            var form = {};
            form.patient_id = $scope.patient_id;
            form.cproblem = problem;
            form.type = type;
            patientService.addCommonProblem(form).then(function (response) {
                let data = response.data;
                if (data['success']) {
                    toaster.pop('success', 'Done', 'New Problem added successfully');
                    $scope.problems.push(data['problem']);

                    $scope.open_problem(data['problem']);

                } else if (!data['success']) {
                    toaster.pop('error', 'Error', data['msg']);
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong');
                }
            });
        }

        function changeTodoList(list, todo) {
            patientService.toggleTodoStatus(todo);
        }

        function openProblem(problem) {
            if (!$scope.draggedProblem) {
                $location.path('/problem/' + problem.id);
            }
        }

        function permitted(permissions) {
            if ($scope.active_user === undefined) {
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

        // label problem list
        function addNewListLabel(new_list, label) {
            var index = new_list.labels.indexOf(label);
            if (index > -1)
                new_list.labels.splice(index, 1);
            else
                new_list.labels.push(label);
        }

        function addProblemList(form) {
            form.user_id = $scope.user_id;
            form.patient_id = $scope.patient_id;
            if (form.name && form.labels.length > 0) {
                problemService.addProblemList(form).then(function (response) {
                    let data = response.data;
                    var new_list = data['new_list'];
                    $scope.problem_lists.push(new_list);
                    $scope.new_list = {};
                    $scope.new_list.labels = [];
                    toaster.pop('success', 'Done', 'New Problem List added successfully');
                });
            } else {
                toaster.pop('error', 'Error', 'Please select name and labels');
            }
        }

        function setCollapse(list) {
            if (list.rename === false)
                list.collapse = !list.collapse;
        }

        function deleteList(list) {
            prompt({
                "title": "Are you sure?",
                "message": "Deleting a problem list is forever. There is no undo."
            }).then(function (result) {
                problemService.deleteProblemList(list).then(function (response) {
                    let data = response.data;
                    var index = $scope.problem_lists.indexOf(list);
                    $scope.problem_lists.splice(index, 1);
                    toaster.pop('success', 'Done', 'Problem List removed successfully');
                });
            }, function () {
                return false;
            });
        }

        function renameList(list) {
            if (list.name) {
                problemService.renameProblemList(list).then(function (response) {
                    let data = response.data;
                    list.rename = false;
                    toaster.pop('success', 'Done', 'Problem List renamed successfully');
                });
            } else {
                toaster.pop('error', 'Error', 'Please input name!');
            }
        }

        function updateProblemListNote(list) {
            var form = {
                'list_id': list.id,
                'note': list.note
            };
            problemService.updateProblemListNote(form).then(function (response) {
                let data = response.data;
                toaster.pop('success', 'Done', 'Problem list note updated!');
            });
        }

        function checkProblemListAuthenticated(list) {
            var is_existed = false;
            angular.forEach(list.problems, function (value, key) {
                if (!value.authenticated) {
                    is_existed = true;
                }
            });
            return is_existed;
        }

        function checkProblemListControlled(list) {
            var is_existed = false;
            angular.forEach(list.problems, function (value, key) {
                if (!value.is_controlled) {
                    is_existed = true;
                }
            });
            return is_existed;
        }

        function inArray(array, item) {
            var is_existed = false;
            angular.forEach(array, function (list, key2) {
                angular.forEach(list.problems, function (value, key) {
                    if (value.id === item.id) {
                        is_existed = true;
                    }
                });
            });
            return is_existed;
        }

        function isInArray(array, item) {
            var is_existed = false;
            angular.forEach(array, function (value, key2) {
                if (value === item) {
                    is_existed = true;
                }
            });
            return is_existed;
        }

        function checkSharedProblem(problem, sharing_patients) {
            if ($scope.patient_id === $scope.user_id || ($scope.active_user.hasOwnProperty('role') && $scope.active_user.role !== 'patient')) {
                return true;
            } else {
                var is_existed = false;
                angular.forEach(sharing_patients, function (p, key) {
                    if (!is_existed && p.user.id === $scope.user_id) {
                        is_existed = $scope.isInArray(p.problems, problem.id);
                    }
                });
                return is_existed;
            }
        }

        // note on header of page
        function updatePatientNote() {
            var form = {
                'patient_id': $scope.patient_id,
                'note': $scope.patient_info.note
            };
            patientService.updatePatientNote(form).then(function (response) {
                let data = response.data;
                toaster.pop('success', 'Done', 'Patient note updated!');
            });
        }

        // encounter
        function unmarkFavoriteEvent(encounter_event) {
            var form = {};
            form.encounter_event_id = encounter_event.id;
            form.is_favorite = false;
            encounterService.markFavoriteEvent(form).then(function (response) {
                let data = response.data;
                $scope.favorites.splice($scope.favorites.indexOf(encounter_event), 1);
                toaster.pop('success', 'Done', 'Unmarked favorite!');
            });
        }

        function nameFavoriteEvent(encounter_event) {
            var form = {};
            form.encounter_event_id = encounter_event.id;
            form.name_favorite = encounter_event.name_favorite;
            encounterService.nameFavoriteEvent(form).then(function (response) {
                let data = response.data;
                encounter_event.is_named = false;
                toaster.pop('success', 'Done', 'Named favorite!');
            });
        }

        /*
         *   handle cache homepage tabs
         */
        function changeHomepageTab(tab) {

            CollapseService.ChangeHomepageTab(tab);

            if ($scope.collapse.show_homepage_tab === "data") {
                var form = {};
                form.patient_id = $scope.patient_id;
                patientService.trackDataClickEvent(form);
            }
            if ($scope.collapse.show_homepage_tab === "mystory") {
                $scope.$broadcast('tabPressed', null);
            }
        }

        function toggleAddMyStoryTab() {
            $scope.show_add_my_story_tab = !$scope.show_add_my_story_tab;
        }

        function addMyStoryTab(new_tab) {
            if (new_tab.name) {
                var form = {};
                form.name = new_tab.name;
                if ($scope.active_user.role === 'patient')
                    form.private = new_tab.private;
                if ($scope.active_user.role === 'admin' || $scope.active_user.role === 'physician')
                    form.all_patients = new_tab.all_patients;
                form.patient_id = $scope.patient_id;
                patientService.addMyStoryTab(form).then(function (response) {
                    let data = response.data;
                    if (data['success'] === true) {
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
        }

        /*
         *   toggle view my story tab
         */
        function viewMyStoryTab(tab) {


            $scope.selected_tab = tab;
            $scope.show_edit_my_story_tab = false;
        }

        /*
         *   toggle add my story text
         */
        function toggleAddMyStoryText() {
            $scope.show_add_my_story_text = !$scope.show_add_my_story_text;
        }

        function addMyStoryText(tab, new_text) {
            var form = {};
            form.name = new_text.name;
            form.text = new_text.text;
            if ($scope.active_user.role === 'patient')
                form.private = new_text.private;
            if (tab.is_all && ($scope.active_user.role === 'admin' || $scope.active_user.role === 'physician'))
                form.all_patients = new_text.all_patients;
            form.concept_id = new_text.concept_id;
            form.patient_id = $scope.patient_id;
            form.tab_id = tab.id;
            patientService.addMyStoryText(form).then(function (response) {
                let data = response.data;
                if (data['success'] === true) {
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
        }

        /*
         *   toggle edit my story tab
         */
        function editMyStoryTab() {
            $scope.show_edit_my_story_tab = !$scope.show_edit_my_story_tab;
        }

        /*
         *   delete my story tab
         */
        function deleteMyStoryTab(selected_tab) {
            prompt({
                "title": "Are you sure?",
                "message": "Deleting a tab is forever. There is no undo."
            }).then(function (result) {
                patientService.deleteMyStoryTab($scope.patient_id, selected_tab.id).then(function (response) {
                    let data = response.data;
                    if (data['success'] === true) {
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
        }

        function saveMyStoryTab(selected_tab) {
            if (selected_tab.name) {
                var form = {};
                form.name = selected_tab.name;
                form.tab_id = selected_tab.id;
                form.patient_id = $scope.patient_id;
                patientService.saveMyStoryTab(form).then(function (response) {
                    let data = response.data;
                    if (data['success'] === true) {
                        $scope.show_edit_my_story_tab = false;
                        toaster.pop('success', "Done", "Saved tab successfully!");
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            } else {
                toaster.pop('error', "Error", "Please input name!");
            }
        }

        /*
         *   delete my story tab
         */
        function deleteMyStoryText(component) {
            prompt({
                "title": "Are you sure?",
                "message": "Deleting a text component is forever. There is no undo."
            }).then(function (result) {
                patientService.deleteMyStoryText($scope.patient_id, component.id).then(function (response) {
                    let data = response.data;
                    if (data['success'] === true) {
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
        }

        function saveMyStoryText(component) {
            var form = {};
            form.name = component.name;
            form.concept_id = component.concept_id;
            form.component_id = component.id;
            form.patient_id = $scope.patient_id;
            patientService.saveMyStoryText(form).then(function (response) {
                let data = response.data;
                if (data['success'] === true) {
                    toaster.pop('success', "Done", "Saved text component successfully!");
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });
        }

        function changeComponentText(component, entry, oldText) {
            var form = {};
            form.text = entry.text;
            form.component_id = component.id;
            form.entry_id = entry.id;
            form.patient_id = $scope.patient_id;
            patientService.saveMyStoryTextEntry(form).then(function (response) {
                let data = response.data;
                if (data['success'] === true) {
                    component.text_component_entries.unshift(data['entry']);
                    if (typeof oldText !== 'undefined')
                        entry.text = oldText;
                    toaster.pop('success', "Done", "Saved text component successfully!");
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });
        }

        function seePreviousEntries() {
            $scope.show_previous_entries = !$scope.show_previous_entries;
        }

        function checkSharedMyStory() {
            if ($scope.active_user) {
                if ($scope.patient_id === $scope.user_id || $scope.active_user.role !== 'patient') {
                    return true;
                } else {
                    var is_shared = false;
                    angular.forEach($scope.sharing_patients, function (user, key) {
                        if (user.id === $scope.active_user.id && user.is_my_story_shared) {
                            is_shared = true;
                        }
                    });
                    return is_shared;
                }
            }
            return false;
        }

        function toggleAddNewDataType() {
            $scope.show_add_new_data_type = !$scope.show_add_new_data_type;
        }

        function addNewDataType(new_data_type) {
            var form = {};
            form.name = new_data_type.name;
            form.code = new_data_type.code;
            form.unit = new_data_type.unit;
            form.color = new_data_type.color;
            form.patient_id = $scope.patient_id;
            patientService.addNewDataType(form).then(function (response) {
                let data = response.data;
                if (data['success'] === true) {
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
        }

        function checkHasDataLoincCode(datas, code) {
            var is_inr = false;
            angular.forEach(datas, function (data, key) {
                angular.forEach(data.observation_components, function (component, key2) {
                    if (component.component_code === code) {
                        is_inr = true;
                    }
                });
            });
            return is_inr;
        }

        function addBfdiValue(component, resetNewValue) {
            // Default is true
            resetNewValue = _.isUndefined(resetNewValue);
            var new_data = {};
            new_data.datetime = moment().format("MM/DD/YYYY HH:mm");
            new_data.value = component.new_value;
            dataService.addData($scope.patient_id, component.id, new_data)
                .then(function (response) {
                    let data = response.data;
                    if (data['success']) {
                        toaster.pop('success', 'Done', 'Added data!');
                        angular.forEach($scope.datas, function (sdata, data_key) {
                            angular.forEach(sdata.observation_components, function (scomponent, component_key) {
                                if (scomponent.id === component.id) {
                                    scomponent.observation_component_values.push(data['value']);
                                }
                            });
                            // Default graph type
                            if (sdata.graph == null)
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
                        // Reset component value
                        // TODO: 2/18/2017 AnhDN temporary disable auto delete new component value
                        if (resetNewValue)
                            component.new_value = '';
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, please try again!');
                    }
                }, function (error) {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                });
        }

        function fileUploadSuccess(resp) {
            $window.open('/#/manage/document/' + resp.data.document, '_blank');
        }

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
                if (key === 0) {
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

        /**
         * Update user summary
         * Refer: https://trello.com/c/K1Thtn7f
         */
        function updateSummary() {
            var form = {
                'patient_id': $scope.patient_id,
                'summary': $scope.patient_info.summary
            };
            patientService.updatePatientSummary(form).then(function (response) {
                let data = response.data;
                toaster.pop('success', 'Done', 'Patient summary updated!');
            });
        }

        function nurseSubmitBDFI() {
            // Last submitted value is haven't modified yet. So user will be asked for confirmation
            if ($scope.btnBDFISubmitted) {
                let reSubmitConfirmationDialogPromise = ngDialog.openConfirm({
                    template: 'reSubmitConfirmDialog',
                    showClose: false,
                    closeByDocument: false,
                    closeByEscape: false
                });

                // If user is confirmed then do submit, otherwise ignored it
                reSubmitConfirmationDialogPromise.then(doSubmitVitals, () => {
                })
            } else {
                doSubmitVitals();
            }

            function doSubmitVitals() {

                let components = _.pluck($scope.mostCommonData, 'observation_components');
                angular.forEach(_.flatten(components), function (value, key) {
                    // Only submit data which is not empty
                    if (_.isUndefined(value.new_value) || _.isEmpty(value.new_value)) {
                        return;
                    }
                    $scope.add_bfdi_value(value, false);
                });
                $scope.btnBDFISubmitted = true;
            }
        }

        /**
         * TODO: Shouldn't manipulate DOM element in the controller
         * */
        function addProblemIsSelected() {
            $timeout(() => {
                $("#problemTermInput").focus();
            }, 200)
        }

        function bdfiValueIsChanged(component) {
            if ($scope.btnBDFISubmitted) {
                $scope.btnBDFISubmitted = false;
                let components = _.pluck($scope.mostCommonData, 'observation_components');
                angular.forEach(_.flatten(components), function (value, key) {
                    if (component.id !== value.id)
                        value.new_value = "";
                });
            }
        }

        /**
         *
         */
        function loadMoreNarrative() {
            $scope.showNarrative = !$scope.showNarrative;
            patientService.loadAllNarrative($scope.patient_id).then(response => {
                $scope.narrativeHistories = response.data;
            });
        }

        /**
         *
         */
        function addNarrative() {
            patientService.addNarrative($scope.patient_id, $scope.narratives.latest)
                .then(response => {
                    $scope.narratives.latest = response.data;
                    $scope.narrativeHistories.unshift(response.data);
                    $scope.narratives.total++;
                });
        }
    }

    /* End of controller */
})();
