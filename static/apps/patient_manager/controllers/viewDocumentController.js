(function () {
    'use strict';
    angular.module('ManagerApp')
        .controller('ViewDocumentCtrl', ViewDocumentCtrl);

    ViewDocumentCtrl.$inject = ['$scope', 'sharedService', '$routeParams', 'patientService', '$location', 'toaster', 'documentService', 'ngDialog'];

    /**
     * WIP: Missing status return
     * @param $scope
     * @param sharedService
     * @param $routeParams
     * @param patientService
     * @param $location
     * @param toaster
     * @constructor
     */
    function ViewDocumentCtrl($scope, sharedService, $routeParams, patientService, $location, toaster, documentService, ngDialog) {

        // PROPERTIES DEFINITION
        $scope.patient_id = $('#patient_id').val();     // Patients are being managed
        $scope.user_id = $('#user_id').val();           // Current logged in id
        $scope.enableTodoPin = false;
        $scope.enableProblemPin = false;
        $scope.labels = [];

        $scope.init = init;
        $scope.deleteDocument = deleteDocument;
        $scope.getPatientInfo = getPatientInfo;
        $scope.open_problem = open_problem;

        $scope.init();


        // METHODS DEFINITION(Only dedicate to service/factory todo business flow)
        function open_problem(problem) {
            $location.path('/problem/' + problem.id);
        }

        // Pin a todo to document
        $scope.pinTodo2Document = function (document, todo) {
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
        };

        $scope.unpinDocumentTodo = function (document, todo) {
            sharedService.unpinDocumentTodo(document, todo).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Msg when success');
                    todo.is_pinned = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            })
        };

        // Pin a problem to document
        $scope.pinProblem2Document = function (document, prob) {
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
        };

        // Unpin a problem to document
        $scope.unpinDocumentProblem = function (document, prob) {
            sharedService.unpinDocumentProblem(document, prob).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Remove problem successfully');
                    prob.is_pinned = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            })
        };

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

            patientService.fetchPatientTodos(patientId).then(function (data) {
                $scope.active_todos = data['pending_todos']; // aka active todo

                // TODO: Is this task is correct place
                var document_todo_pk = _.pluck($scope.document.todos, 'id');
                _.map($scope.active_todos, function (value, key) {
                    value.is_pinned = _.contains(document_todo_pk, value.id);
                })
            });

            // Fetch user's problem
            patientService.fetchProblems(patientId).then(function (response) {
                $scope.active_probs = response.problems;

                // TODO: Is this task is correct place
                var document_problem_pk = _.pluck($scope.document.problems, 'id');
                _.map($scope.active_probs, function (value, key) {
                    value.is_pinned = _.contains(document_problem_pk, value.id)
                });
            });
        }

        /**
         * Initialize data for this view document page
         */
        function init() {

            sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
                $scope.document = resp.data.info;

                $scope.labels = resp.data.labels;

                // TODO: Is this task is correct place
                var document_label_pk = _.pluck($scope.document.labels, 'id');
                _.map($scope.labels, function (value, key, list) {
                    value.is_pinned = _.contains(document_label_pk, value.id);
                });

                // Loading all related
                if (resp.data.info.patient != null) {
                    var patientId = resp.data.info.patient.user.id;
                    $scope.getPatientInfo(patientId);
                }

            });

            // Refer https://trello.com/c/fDYvV4z6
            sharedService.getUploadedDocument().then(function (response) {
                $scope.uploadedDocuments = response.data.documents;
            });

        }
    }
})();