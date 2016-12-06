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
            staffService.fetchProblems(patientId).then(function (response) {
                $scope.active_probs = response.problems;
            });
            // Fetch user's todos
            staffService.fetchPatientTodos(patientId).then(function (data) {
                $scope.active_todos = data['pending_todos']; // aka active todo
            });
        }

        documentService.getDocumentInfo($routeParams.documentId).then(function (resp) {
            $scope.document = resp.data.info;
            var document_label_pk = _.pluck($scope.document.labels, 'id');
            $scope.labels = resp.data.labels;
            _.map($scope.labels, function (value, key, list) {
                if (_.contains(document_label_pk, value.id))
                    value.is_pinned = true;
            });

            // Loading all related 
            if (resp.data.info.patient != null) {
                var patientId = resp.data.info.patient.user.id;
                getPatientInfo(patientId);
            }
        });


        // Status
        $scope.pinTodo2Document = function (document, todo) {
            documentService.pinTodo2Document(document, todo)
                .then(function (response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Added todo to document')
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                }, function (resp) {
                    // error occurred
                });
        };

        // Status
        $scope.pinProblem2Document = function (document, prob) {
            documentService.pinProblem2Document(document, prob)
                .then(function (response) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Document is pinned to problem')
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong!');
                    }
                }, function (response) {
                    // error occurred
                });
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
                .then(function (resp) {
                    if (response.data.success) {
                        toaster.pop('success', 'Done', 'Added label to document')
                        $scope.document = resp.data.info;
                        var patientId = resp.data.info.patient.user.id;
                        getPatientInfo(patientId);
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
        $scope.add_label_to_document = function (document, label) {
            sharedService.add_label_2_document(document, label).then(function (response) {
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
        $scope.remove_document_label = function (document, label) {
            sharedService.remove_document_label(document, label).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', "Removed document's label")
                    label.is_pinned = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            });
        };
    }
})();