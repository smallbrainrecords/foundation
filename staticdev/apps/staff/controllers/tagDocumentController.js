(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('TagDocumentCtrl', TagDocumentCtrl);

    TagDocumentCtrl.$inject = ['$scope', 'documentService', '$routeParams', 'staffService', '$http', 'toaster', '$cookies', 'sharedService'];

    /**
     * WIP: Missing status return
     * @param $scope
     * @param documentService
     * @param $routeParams
     * @param staffService
     * @param $http
     * @param toaster
     * @param $cookies
     * @param sharedService
     * @constructor
     */
    function TagDocumentCtrl($scope, documentService, $routeParams, staffService, $http, toaster, $cookies, sharedService) {

        function getPatientInfo(patientId) {
            // Fetch user's todos
            staffService.fetchPatientTodos(patientId).then(function (data) {
                $scope.active_todos = data['pending_todos']; // aka active todo

                // TODO: Is this task is correct place
                var document_todo_pk = _.pluck($scope.document.todos, 'id');
                _.map($scope.active_todos, function (value, key) {
                    value.is_pinned = _.contains(document_todo_pk, value.id);
                })
            });

            // Fetch user's problem
            staffService.fetchProblems(patientId).then(function (response) {
                $scope.active_probs = response.problems;

                // TODO: Is this task is correct place
                var document_problem_pk = _.pluck($scope.document.problems, 'id');
                _.map($scope.active_probs, function (value, key) {
                    value.is_pinned = _.contains(document_problem_pk, value.id)
                });
            });
        }

        documentService.getDocumentInfo($routeParams.documentId).then(function (resp) {
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
                getPatientInfo(patientId);
            }
        });


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


        $scope.getPatients = function (viewValue) {
            return $http.post('/docs/search_patient', {
                search_str: viewValue
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            }).then(function (response) {
                return response.data.results;
            });
        };

        //TODO Implement details here
        $scope.pinPatient2Document = function (item, model) {
            documentService.pinPatient2Document($scope.document, model)
                .then(function (response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Added label to document. Loading patient todo and patient');
                        $scope.document = response.data.info;
                        getPatientInfo(response.data.info.patient.user.id);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }, function (error) {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                })
        };


        /**
         * @param document
         * @param label
         */
        $scope.pinLabelToDocument = function (document, label) {
            sharedService.pinLabelToDocument(document, label).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Added label to document');
                    label.is_pinned = true;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            });
        };

        /**
         *
         * @param document
         * @param label
         */
        $scope.unpinDocumentLabel = function (document, label) {
            sharedService.unpinDocumentLabel(document, label).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', "Removed document's label");
                    label.is_pinned = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            });
        };
    }
})();