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
            if (resp.data.info.patient != null) {
                var patientId = resp.data.info.patient.user.id;
                getPatientInfo(patientId);
            }
        });


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
                    $scope.document = resp.data.info;
                    var patientId = resp.data.info.patient.user.id;
                    getPatientInfo(patientId);
                }, function (error) {

                })
        };
    }
})();