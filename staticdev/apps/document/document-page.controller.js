(function () {
    'use strict';
    angular.module('document')
        .controller('ViewDocumentCtrl', ViewDocumentCtrl);

    ViewDocumentCtrl.$inject = ['$scope', 'sharedService', '$routeParams', '$location', 'toaster', 'documentService', 'ngDialog', '$http', '$cookies', 'todoService'];

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
     * @constructor
     */
    function ViewDocumentCtrl($scope, sharedService, $routeParams, $location, toaster, documentService, ngDialog, $http, $cookies, todoService) {

        // PROPERTIES DEFINITION
        $scope.patient_id = $('#patient_id').val();     // Patients are being managed
        $scope.user_id = $('#user_id').val();           // Current logged in id
        $scope.document = {};
        $scope.labels = [];
        $scope.newDocumentName = "";
        $scope.patientSearchString = "";
        $scope.enableEditDocumentName = false;
        $scope.enableTodoPin = false;
        $scope.enableProblemPin = false;
        $scope.enableEditLabel = false;
        $scope.enableEditPatient = false;
        $scope.new_todo = {};
        $scope.new_problem = {set: false};

        $scope.deleteDocument = deleteDocument;
        $scope.getPatientInfo = getPatientInfo;
        $scope.open_problem = open_problem;
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

        // TODO: Create todo-add component based
        $scope.addTodo = addTodo;

        // TODO: Create problem-add component based
        $scope.addNewCommonProblem = addNewCommonProblem;


        $scope.problemTermChanged = problemTermChanged;
        $scope.set_new_problem = setNewProblem;
        $scope.unset_new_problem = unset_new_problem;
        $scope.add_problem = add_problem;
        $scope.add_new_problem = add_new_problem;

        init();

        function init() {

            sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
                $scope.document = resp.data.info;
                $scope.newDocumentName = $scope.document.document_name;
                $scope.labels = resp.data.labels;

                var document_label_pk = _.pluck($scope.document.labels, 'id');
                _.map($scope.labels, function (value, key, list) {
                    value.is_pinned = _.contains(document_label_pk, value.id);
                });

                // Loading all related
                if ($scope.document.patient != null) {
                    $scope.patient_id = $scope.document.patient.user.id;
                    $scope.getPatientInfo($scope.patient_id);

                    sharedService.fetchPatientInfo($scope.patient_id).then(function (response) {
                        $scope.patient = response.data;
                        $scope.acutes = response.data.acutes_list;
                        $scope.chronics = response.data.chronics_list;
                    });
                }
            });

            sharedService.fetchActiveUser().then(function (response) {
                // Logged in user profile in Django authentication system
                $scope.active_user = response.data['user_profile'];
            });

            todoService.fetchTodoMembers($scope.patient_id).then(function (data) {
                $scope.members = data['members'];
            });
        }

        // METHODS DEFINITION(Only dedicate to service/factory todo business flow)
        function open_problem(problem) {
            $location.path('/problem/' + problem.id);
        }

        // Pin a todo to document
        function pinTodo2Document(document, todo) {
            documentService.pinTodo2Document(document, todo)
                .then(function (response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Added todo to document');
                        todo.is_pinned = true;
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                }, function (resp) {
                    // error occurred
                });
        }

        function unpinDocumentTodo(document, todo) {
            sharedService.unpinDocumentTodo(document, todo).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Msg when success');
                    todo.is_pinned = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            })
        }

        // Pin a problem to document
        function pinProblem2Document(document, prob) {
            documentService.pinProblem2Document(document, prob)
                .then(function (response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Document is pinned to problem');
                        prob.is_pinned = true;
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }, function (response) {
                    // error occurred
                });
        }

        // Unpin a problem to document
        function unpinDocumentProblem(document, prob) {
            sharedService.unpinDocumentProblem(document, prob).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Remove problem successfully');
                    prob.is_pinned = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
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

            sharedService.fetchPatientTodos(patientId).then(function (response) {
                $scope.active_todos = response.data['pending_todos']; // aka active todo

                // TODO: Is this task is correct place
                var document_todo_pk = _.pluck($scope.document.todos, 'id');
                _.map($scope.active_todos, function (value, key) {
                    value.is_pinned = _.contains(document_todo_pk, value.id);
                })
            });

            // Fetch user's problem
            sharedService.fetchProblems(patientId).then(function (response) {
                $scope.active_probs = response.data.problems;

                // TODO: Is this task is correct place
                var document_problem_pk = _.pluck($scope.document.problems, 'id');
                _.map($scope.active_probs, function (value, key) {
                    value.is_pinned = _.contains(document_problem_pk, value.id)
                });
            });
        }

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

                    label.is_pinned = true;

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

                    label.is_pinned = false;

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

        function addTodo(form) {
            if (form == undefined || form.name.trim().length < 1) {
                return false;
            }
            form.patient_id = $scope.patient_id;

            if ($scope.patient['bleeding_risk']) {
                var bleedingRiskDialog = ngDialog.open({
                    template: 'bleedingRiskDialog',
                    showClose: false,
                    closeByEscape: false,
                    closeByDocument: false,
                    closeByNavigation: false
                });

                bleedingRiskDialog.closePromise.then(askDueDate);
            } else {
                askDueDate();
            }

            function askDueDate() {
                var acceptedFormat = ['MM/DD/YYYY', "M/D/YYYY", "MM/YYYY", "M/YYYY", "MM/DD/YY", "M/D/YY", "MM/YY", "M/YY"];

                var dueDateDialog = ngDialog.open({
                    template: 'postAddTodoDialog',
                    showClose: false,
                    closeByDocument: false,
                    closeByNavigation: false,
                    closeByEscape: false,// Added ignore close by escape to prevent user can not see the tag member step,
                    scope: $scope,
                    controller: function () {
                        var vm = this;
                        vm.step = 0;
                        vm.form = {
                            dueDate: "",
                            taggedMembers: []
                        };

                        vm.dueDateIsValid = true;
                        vm.memberSearch = "";
                        // Member will be passed down from parent controller
                        vm.memberList = $scope.members;

                        vm.dueDateValidation = dueDateValidation;
                        vm.toggleTaggedMember = toggleTaggedMember;
                        vm.memberFilter = memberFilter;

                        /**
                         * Filter is case sensitive
                         * @param item
                         * @returns {boolean}
                         */
                        function memberFilter(item) {
                            return item.user.first_name.indexOf(vm.memberSearch) !== -1 || item.user.last_name.indexOf(vm.memberSearch) !== -1;
                        }

                        /**
                         *
                         * @param member
                         */
                        function toggleTaggedMember(member) {
                            let idx = vm.form.taggedMembers.indexOf(member.id);
                            idx === -1 ? vm.form.taggedMembers.push(member.id) : vm.form.taggedMembers.splice(idx, 1);
                        }

                        /**
                         * Validate user entried todo's due date
                         */
                        function dueDateValidation() {
                            vm.dueDateIsValid = _.isEmpty(vm.form.dueDate) ? true : moment(vm.form.dueDate, acceptedFormat, true).isValid();
                        }
                    },
                    controllerAs: 'vm'
                });
                dueDateDialog.closePromise.then(data => {
                    if (data.value.due_date)
                        form.due_date = moment(data.value.dueDate, acceptedFormat).toString();
                    form.members = data.value.taggedMembers;

                    sharedService.addToDo(form).then(addTodoSuccess);
                });
            }

            // Add todo succeeded
            function addTodoSuccess(response) {
                toaster.pop('success', 'Done', 'Added Todo!');

                $scope.pinTodo2Document($scope.document, response.todo);

                $scope.active_todos.push(response.todo);

                $scope.new_todo = {};

                $('#todoNameInput').val("");
                $('#todoNameInput').focus();
            }
        }

        function addNewCommonProblem(problem, type) {
            var form = {};
            form.patient_id = $scope.patient_id;
            form.cproblem = problem;
            form.type = type;

            sharedService.addCommonProblem(form).then(addProblemSuccess, addProblemFailed);

            function addProblemSuccess(response) {

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


        function setNewProblem(problem) {
            $scope.new_problem.set = true;
            $scope.new_problem.active = problem.active;
            $scope.new_problem.term = problem.term;
            $scope.new_problem.code = problem.code;

        }

        function unset_new_problem() {
            $scope.new_problem.set = false;
        }

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

        function pinPatient2Document(item, model) {
            documentService.pinPatient2Document($scope.document, model)
                .then(function (response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Added label to document. Loading patient todo and patient');
                        $scope.document = response.data.info;
                        $scope.getPatientInfo(response.data.info.patient.user.id);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }, function (error) {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                })
        }
    }
})();