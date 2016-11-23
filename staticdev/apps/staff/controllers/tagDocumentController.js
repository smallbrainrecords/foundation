(function () {
    'use strict';
    angular.module('StaffApp')
        .controller('TagDocumentCtrl', TagDocumentCtrl);

    TagDocumentCtrl.$inject = ['$scope', 'documentService', '$routeParams', 'staffService'];

    /**
     *
     * @param $scope
     * @param documentService
     * @param $routeParams
     * @param staffService
     * @constructor
     */
    function TagDocumentCtrl($scope, documentService, $routeParams, staffService) {

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

        $scope.pinDocument2Patient = pinDocument2Patient;

        $scope.pinDocument2Todo = documentService.pinDocument2Todo;
        $scope.pinDocument2Problem = documentService.pinDocument2Problem;
        function pinDocument2Patient() {
            //TODO Implement details here
        }
    }
})();