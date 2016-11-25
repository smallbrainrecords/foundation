(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('TagDocumentCtrl', TagDocumentCtrl);

    TagDocumentCtrl.$inject = ['$scope', 'documentService', '$routeParams', 'staffService', '$http', '$cookies'];

    /**
     * WIP: Missing status return
     * @param $scope
     * @param documentService
     * @param $routeParams
     * @param staffService
     * @constructor
     */
    function TagDocumentCtrl($scope, documentService, $routeParams, staffService, $http, $cookies) {

        documentService.getDocumentInfo($routeParams.documentId).then(function (resp) {
            $scope.document = resp.data.info;
            if (resp.data.info.patient != null) {
                // Fetch user's probs
                var patientId = resp.data.info.patient.id;
                staffService.fetchProblems(patientId).then(function (response) {
                    $scope.active_probs = response.problems;
                });
                // Fetch user's todos
                staffService.fetchPatientTodos(patientId).then(function (data) {
                    $scope.active_todos = data['pending_todos']; // aka active todo
                });
            }
        });

        $scope.getPatients = function (viewValue) {
            return $http.post('/docs/search_patient', {
                search_str: viewValue
            }, {
                headers: {
                    'X-CSRFToken': $cookies.csrftoken
                }
            }).then(function (response) {
                return response.data.results.map(function (item) {
                    return item.first_name + " " + item.last_name;
                });
            });
        };

        // Status
        $scope.pinTodo2Document = function (document, todo) {
            documentService.pinTodo2Document(document, todo)
                .then(function (resp) {
                    // success full pinned to item
                }, function (resp) {
                    // error occurred
                });
        };

        // Status
        $scope.pinProblem2Document = function (document, prob) {
            documentService.pinProblem2Document(document, prob)
                .then(function (resp) {
                    // success full pinned to item
                }, function (resp) {
                    // error occurred
                });
        };

        //TODO Implement details here
        $scope.pinPatient2Document = function (document, patient) {
            documentService.pinPatient2Document(document, patient)
                .then(function (success) {
                    staffService.fetchProblems(patient.id).then(function (response) {
                        $scope.active_probs = response.problems;
                    });

                    // Fetch user's todos
                    staffService.fetchPatientTodos(patient.id).then(function (data) {
                        $scope.active_todos = data['pending_todos']; // aka active todo
                    });
                }, function (error) {

                })
        };

        $scope.patients = ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Dakota', 'North Carolina', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'];
    }
})();