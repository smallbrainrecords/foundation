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
    angular.module('document', ['ngFileUpload', 'toaster', 'sharedModule', 'httpModule','app.services'])
        .controller('ViewDocumentCtrl', ViewDocumentCtrl);

    ViewDocumentCtrl.$inject = ['$scope', 'sharedService', '$routeParams', '$location', 'toaster', 'documentService', 'ngDialog', '$http', '$cookies', 'todoService', '$window'];

    /**
     * @param $scope
     * @param sharedService
     * @param $routeParams
     * @param $location
     * @param toaster
     * @param documentService
     * @param ngDialog
     * @param $http
     * @param $cookies
     * @param todoService
     * @param $window
     * @constructor
     */
    function ViewDocumentCtrl($scope, sharedService, $routeParams, $location, toaster, documentService, ngDialog, $http, $cookies, todoService, $window) {

        // PROPERTIES DEFINITION
        $scope.document = {};
        $scope.labels = [];
        $scope.newDocumentName = "";
        $scope.patientSearchString = "";
        $scope.enableEditDocumentName = false;
        $scope.enableTodoPin = false;
        $scope.enableProblemPin = false;
        $scope.enableEditLabel = true;
        $scope.enableEditPatient = false;
        $scope.new_todo = {};
        $scope.new_problem = {set: false};
        $scope.indirectPinnedProblem = [];

        $scope.deleteDocument = deleteDocument;
        $scope.getPatientInfo = getPatientInfo;
        $scope.pinTodo2Document = pinTodo2Document;
        $scope.unpinDocumentTodo = unpinDocumentTodo;
        $scope.pinProblem2Document = pinProblem2Document;
        $scope.unpinDocumentProblem = unpinDocumentProblem;
        $scope.updateDocumentName = updateDocumentName;
        $scope.pinLabelToDocument = pinLabelToDocument;
        $scope.unpinDocumentLabel = unpinDocumentLabel;
        $scope.getPatients = getPatients;
        $scope.pinPatient2Document = pinPatient2Document;
        $scope.permitted = permitted;
        $scope.addTodo = addTodo;
        $scope.addNewCommonProblem = addNewCommonProblem;
        $scope.problemTermChanged = problemTermChanged;
        $scope.set_new_problem = setNewProblem;
        $scope.unset_new_problem = unset_new_problem;
        $scope.add_problem = add_problem;
        $scope.add_new_problem = add_new_problem;
        $scope.isDueDate = isDueDate;

        init();

        function init() {

            sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
                $scope.document = resp.data.info;
                $scope.newDocumentName = $scope.document.document_name;
                $scope.labels = resp.data.labels;

                var document_label_pk = _.pluck($scope.document.labels, 'id');
                _.map($scope.labels, function (value, key, list) {
                    value.pin = _.contains(document_label_pk, value.id);
                });

                // Get all indirect problem pinned to the document
                _.map($scope.document.todos, (ele, idx) => {
                    if (ele.problem && !_.contains($scope.indirectPinnedProblem, ele.problem.id))
                        $scope.indirectPinnedProblem.push(ele.problem.id);
                });

                // Loading all related
                if ($scope.document.patient !== null) {
                    $scope.patient_id = $scope.document.patient.id;
                    $scope.getPatientInfo($scope.patient_id);

                    sharedService.fetchPatientInfo($scope.patient_id).then(function (response) {
                        // $scope.patient = response.data;
                        $scope.acutes = response.data.acutes_list;
                        $scope.chronics = response.data.chronics_list;
                    });
                }
            });

            if ($scope.patient_id)
                todoService.fetchTodoMembers($scope.patient_id).then((data) => {
                    $scope.members = data['members'];
                });
        }

        // METHODS DEFINITION(Only dedicate to service/factory todo business flow)

        /**
         *
         * @param document
         * @param todo
         */
        function pinTodo2Document(document, todo) {
            todo.pin = true;
            document.todos.push(todo);

            documentService.pinTodo2Document(document, todo)
                .then((response) => {
                    response.data.success ? toaster.pop('success', 'Done', 'Added todo to document') : toaster.pop('error', 'Warning', 'Something went wrong!');

                    // If todo is pined to a problem then display the problem in pinned list
                    if (todo.problem !== null) {
                        _.map($scope.active_probs, (ele, idx) => {
                            ele.pin = ele.id === todo.problem.id;
                        })
                    }
                });
        }

        /**
         *
         * @param document
         * @param todo
         */
        function unpinDocumentTodo(document, todo) {
            todo.pin = false;

            // Remove in document array
            _.map(document.todos, (ele, idx) => {
                if (ele.id === todo.id)
                    document.todos.splice(idx, 1);
            });

            // Request to backend stuff
            sharedService.unpinDocumentTodo(document, todo).then(function (response) {
                response.data.success ? toaster.pop('success', 'Done', 'Unpin success') : toaster.pop('error', 'Error', 'Something went wrong!');

                // If todo is pined to a problem and no other document's todo have sample problem
                if (todo.problem !== null) {
                    let todoProblemIsNotIndirectToDocumentByOtherTodo = true;
                    _.map($scope.document.todos, (ele, idx) => {
                        if (ele.problem !== null && ele.problem.id === todo.problem.id)
                            todoProblemIsNotIndirectToDocumentByOtherTodo = false;
                    });

                    let todoProblemIsNotPinDirectly = true;
                    _.map($scope.document.problems, (ele, idx) => {
                        if (ele.id === todo.problem.id)
                            todoProblemIsNotPinDirectly = false;
                    });

                    if (todoProblemIsNotIndirectToDocumentByOtherTodo && todoProblemIsNotPinDirectly) {
                        _.map($scope.active_probs, (ele, idx) => {
                            if (ele.id === todo.problem.id)
                                ele.pin = false;
                        })
                    }
                }
            })
        }

        /**
         *
         * @param document
         * @param prob
         */
        function pinProblem2Document(document, prob) {
            prob.pin = true;

            document.problems.push(prob);

            documentService.pinProblem2Document(document, prob)
                .then((response) => {
                    response.data.success ? toaster.pop('success', 'Done', 'Document is pinned to problem') : toaster.pop('error', 'Error', 'Something went wrong!');
                });
        }

        /**
         *
         * @param document
         * @param prob
         */
        function unpinDocumentProblem(document, prob) {
            prob.pin = false;

            // Remove in document array
            _.map(document.problems, (ele, idx) => {
                if (ele.id === prob.id)
                    document.problems.splice(idx, 1);
            });

            sharedService.unpinDocumentProblem(document, prob)
                .then((response) => {
                    response.data.success ? toaster.pop('success', 'Done', 'Remove problem successfully') : toaster.pop('error', 'Error', 'Something went wrong!');
                })
        }

        /**
         * Delete document
         * @param document
         */
        function deleteDocument(document) {
            // Ask for delete
            var deleteConfirmationDialog = ngDialog.open({
                template: "documentConfirmDialog",
                showClose: false,
                closeByDocument: false,
                closeByNavigation: false
            });

            deleteConfirmationDialog.closePromise.then(function (data) {
                if (data.value)
                    sharedService.removeDocument(document).then(deleteDocumentSuccess, deleteDocumentFailed)
            });


            function deleteDocumentSuccess(response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Document is deleted');

                    // Go back to previous page
                    $location.path('/');
                } else {
                    toaster.pop('error', 'Error', response.data.message);
                }
            }

            function deleteDocumentFailed(error) {
                toaster.pop('error', 'Error', 'Something went wrong. We fix this ASAP');
            }
        }

        /**
         * Fetch user's todos, problems
         * @param patientId
         */
        function getPatientInfo(patientId) {
            sharedService.getTodoList(patientId, false, true)
                .then((response) => {
                    $scope.active_todos = response.data;

                    // Direct pinned todo
                    let document_todo_pk = _.pluck($scope.document.todos, 'id');
                    _.map($scope.active_todos, function (value, key) {
                        value.pin = _.contains(document_todo_pk, value.id);
                    })
                });

            // Fetch user's problem
            sharedService.fetchProblems(patientId)
                .then((response) => {
                    $scope.active_probs = response.data.problems;

                    // Direct pinned problem and Indirect(via todo's problem) pinned problem
                    let document_problem_pk = _.pluck($scope.document.problems, 'id');
                    _.map($scope.active_probs, function (value, key) {
                        value.pin = _.contains(document_problem_pk, value.id) || _.contains($scope.indirectPinnedProblem, value.id);
                    });
                });
        }

        /**
         *
         */
        function updateDocumentName() {

            documentService.updateDocumentName($scope.document.id, {'name': $scope.newDocumentName})
                .then(updateNameSuccess, updateNameFailed);

            function updateNameSuccess(response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Document renamed success');
                    $scope.document.document_name = angular.copy($scope.newDocumentName);
                    $scope.enableEditDocumentName = false;
                    $scope.newDocumentName = "";
                } else {
                    toaster.pop('error', 'Error', response.data.message);
                }
            }

            function updateNameFailed(error) {
                toaster.pop('error', 'Error', 'Something went wrong. We fix this ASAP');
            }
        }


        /**
         * Pin a label to document
         * @param document
         * @param label
         */
        function pinLabelToDocument(document, label) {
            sharedService.pinLabelToDocument(document, label)
                .then(pinLabelSuccess, pinLabelFailed);

            function pinLabelSuccess(response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Added label to document');

                    label.pin = true;

                    document.labels.push(label);
                } else {
                    toaster.pop('error', 'Error', 'Pin label to document failed');
                }
            }

            function pinLabelFailed(response) {
                toaster.pop('error', 'Error', 'Something went wrong. We fix this ASAP');
            }
        }

        /**
         * Remove document labels
         * @param document
         * @param label
         */
        function unpinDocumentLabel(document, label) {
            sharedService.unpinDocumentLabel(document, label).then(unPinLabelSuccess, unPinLabelFailed);

            function unPinLabelSuccess(response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', "Removed document's label");

                    label.pin = false;

                    // Remove label in front-end
                    _.each(document.labels, function (ele, idx) {
                        if (angular.equals(ele.id, label.id))
                            document.labels.splice(idx, 1);
                    });
                } else {
                    toaster.pop('error', 'Error', "Unpin document's label failed");
                }
            }

            function unPinLabelFailed(response) {
                toaster.pop('error', 'Error', 'Something went wrong. We fix this ASAP');
            }
        }

        /**
         * TODO: Migrate to global scope
         * @param permissions
         * @returns {boolean}
         */
        function permitted(permissions) {

            if ($scope.active_user === undefined) {
                return false;
            }

            let user_permissions = $scope.active_user.permissions;

            for (var key in permissions) {

                if (user_permissions.indexOf(permissions[key]) < 0) {
                    return false;
                }
            }

            return true;

        }

        /**
         *
         * @param form
         * @returns {boolean}
         */
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
                }).closePromise.then(function (data) {
                    if (!_.isUndefined(data.value) && '$escape' !== data.value && '$document' !== data.value)
                        form.due_date = moment(data.value, acceptedFormat).toString();
                    sharedService.addToDo(form).then(postAddTodo);
                });
            }

            // Going to
            function postAddTodo(response) {
                if (response.success) {
                    toaster.pop('success', 'Done', 'Added Todo!');

                    var addedTodo = response.todo;
                    $scope.pinTodo2Document($scope.document, addedTodo);
                    $scope.active_todos.push(addedTodo);
                    $scope.new_todo = {};

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

        /**
         *
         * @param problem
         * @param type
         */
        function addNewCommonProblem(problem, type) {
            var form = {};
            form.patient_id = $scope.patient_id;
            form.cproblem = problem;
            form.type = type;

            sharedService.addCommonProblem(form).then(addProblemSuccess, addProblemFailed);

            function addProblemSuccess(data) {

                if (data.success) {
                    toaster.pop('success', 'Done', 'New problem added successfully');

                    $scope.pinProblem2Document($scope.document, response.problem);

                    $scope.active_probs.push(response.problem);
                } else {
                    toaster.pop('error', 'Error', data['msg']);
                }
            }

            function addProblemFailed(error) {
                toaster.pop('error', 'Error', 'Something went wrong');

            }
        }

        /**
         *
         * @param term
         */
        function problemTermChanged(term) {
            // $scope.unset_new_problem();
            $scope.new_problem.set = false;

            if (term.length > 2) {
                sharedService.listTerms(term).then(function (data) {
                    $scope.problem_terms = data;
                });
            } else {
                $scope.problem_terms = [];
            }
        }

        /**
         *
         * @param problem
         */
        function setNewProblem(problem) {
            $scope.new_problem.set = true;
            $scope.new_problem.active = problem.active;
            $scope.new_problem.term = problem.term;
            $scope.new_problem.code = problem.code;

        }

        /**
         *
         */
        function unset_new_problem() {
            $scope.new_problem.set = false;
        }

        /**
         *
         * @returns {boolean}
         */
        function add_problem() {

            var c = confirm("Are you sure?");

            if (c == false) {
                return false;
            }

            var form = {};
            form.patient_id = $scope.patient_id;
            form.term = $scope.new_problem.term;
            form.code = $scope.new_problem.code;
            form.active = $scope.new_problem.active;

            exeAddingProblem(form);
        }

        /**
         *
         * @param problem_term
         * @returns {boolean}
         */
        function add_new_problem(problem_term) {
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

            exeAddingProblem(form);
        }

        /**
         * DRY
         * Final execution for adding new problem either from free text search or select from search result
         * @param form
         */
        function exeAddingProblem(form) {

            sharedService.addProblem(form).then(addProblemSuccess, addProblemFailed);


            function addProblemSuccess(data) {

                if (data.success) {
                    toaster.pop('success', 'Done', 'New Problem added successfully');

                    // Auto-pin
                    $scope.pinProblem2Document($scope.document, data.problem);

                    // Reset model
                    $scope.active_probs.push(data.problem);
                    $scope.problem_term = '';
                    $scope.new_problem = {set: false};

                    /* Not-angular-way */
                    $('#problemTermInput').val("");
                    $('#problemTermInput').focus();
                } else {
                    toaster.pop('error', 'Error', data['msg']);
                }
            }

            function addProblemFailed(error) {
                toaster.pop('error', 'Error', 'Something went wrong');
            }
        }

        /**
         *
         * @param viewValue
         */
        function getPatients(viewValue) {
            return $http.post('/docs/search_patient', {
                search_str: viewValue
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            }).then(function (response) {
                return response.data.results;
            });
        }

        /**
         *
         * @param item
         * @param model
         */
        function pinPatient2Document(item, model) {
            $scope.enableEditPatient = false;

            documentService.pinPatient2Document($scope.document, model)
                .then((response) => {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Added label to document. Loading patient todo and patient');
                        $scope.document = response.data.info;
                        $scope.getPatientInfo(response.data.info.patient.id);

                        $window.location.href = `/u/patient/manage/${response.data.info.patient.id}/#/document/${$scope.document.id}`;
                        $window.reload();
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }, (error) => {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                })
        }

        function isDueDate(date) {
            return moment().isAfter(date) ? 'due-date' : '';
        }
    }
})();