(function () {
    'use strict';
    angular.module('ManagerApp')
        .controller('ViewDocumentCtrl', ViewDocumentCtrl);

    ViewDocumentCtrl.$inject = ['$scope', 'sharedService', '$routeParams', 'patientService', '$location', 'toaster', 'documentService'];

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
    function ViewDocumentCtrl($scope, sharedService, $routeParams, patientService, $location, toaster, documentService) {

        // PROPERTIES DEFINITION
        $scope.patient_id = $('#patient_id').val();     // Patients are being managed
        $scope.user_id = $('#user_id').val();           // Current logged in id
        $scope.enableTodoPin = false;
        $scope.enableProblemPin = false;

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

        // TODO: DRY this method, should move to shared service.
        // function checkSharedProblem(problem, sharing_patients) {
        //     if ($scope.patient_id == $scope.user_id || ($scope.active_user.hasOwnProperty('role') && $scope.active_user.role != 'patient')) {
        //         return true;
        //     } else {
        //         var is_existed = false;
        //         angular.forEach(sharing_patients, function (value, key) {
        //             if (!is_existed && value.user.id == $scope.user_id) {
        //                 is_existed = $scope.isInArray(value.problems, problem.id);
        //             }
        //         });
        //         return is_existed;
        //     }
        // }

        /**
         * Delete document
         * @param document
         */
        function deleteDocument(document) {
            sharedService.removeDocument(document).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Document is deleted');

                    // Go back to previous page
                    $location.path('/');
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            })
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
            //sharedService.initHotkey($scope);

            // patientService.fetchActiveUser().then(function (data) {
            //     $scope.active_user = data['user_profile'];
            //     console.log($scope.active_user);
            // $scope.getPatientInfo($scope.active_user.id);
            // });

            sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
                $scope.document = resp.data.info;

                $scope.getPatientInfo($scope.patient_id);
            });

            // Refer https://trello.com/c/fDYvV4z6
            sharedService.getUploadedDocument().then(function (response) {
                $scope.uploadedDocuments = response.data.documents;
            });

        }
    }
})();