(function () {
    'use strict';
    angular.module('ManagerApp')
        .controller('ViewDocumentCtrl', ViewDocumentCtrl);

    ViewDocumentCtrl.$inject = ['$scope', 'sharedService', '$routeParams', 'patientService', '$location', 'toaster'];

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
    function ViewDocumentCtrl($scope, sharedService, $routeParams, patientService, $location, toaster) {

        // PROPERTIES DEFINITION

        $scope.patient_id = $('#patient_id').val();     // Patients are being managed

        $scope.user_id = $('#user_id').val();           // Current logged in id

        // INITIALIZE DATA FOR THIS PAGE.(Note: It's should be right after property definition due to some method in controller can use the initialized data)
        sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
            $scope.document = resp.data.info;
            $scope.todos_ready = true; // TODO: Should be removed
        });

        sharedService.getUploadedDocument().then(function (response) {
            $scope.uploadedDocuments = response.data.documents;
        });

        patientService.fetchActiveUser().then(function (data) {
            $scope.active_user = data['user_profile'];
        });

        // METHODS DEFINITION(Only dedicate to service/factory todo business flow)

        $scope.open_problem = function (problem) {
            $location.path('/problem/' + problem.id);
        };

        // TODO: DRY this method, should move to shared service.
        $scope.checkSharedProblem = function (problem, sharing_patients) {
            if ($scope.patient_id == $scope.user_id || ($scope.active_user.hasOwnProperty('role') && $scope.active_user.role != 'patient')) {
                return true;
            } else {
                var is_existed = false;
                angular.forEach(sharing_patients, function (value, key) {
                    if (!is_existed && value.user.id == $scope.user_id) {
                        is_existed = $scope.isInArray(value.problems, problem.id);
                    }
                });
                return is_existed;
            }
        };

        /**
         *
         * @param document
         */
        $scope.deleteDocument = function (document) {
            sharedService.removeDocument(document).then(function (response) {
                if (response.data.success) {
                    toaster.pop('success', 'Done', 'Document is deleted');

                    // Go back to previous page
                    $location.path('/');
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong!');
                }
            })
        };
    }
})();