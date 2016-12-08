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

        // Properties definition

        $scope.patient_id = $('#patient_id').val();     // Patients are being managed

        $scope.user_id = $('#user_id').val();           // Current logged in id


        // Methods definition

        $scope.open_problem = function (problem) {
            $location.path('/problem/' + problem.id);
        };

        $scope.checkSharedProblem = function (problem, sharing_patients) {
            if ($scope.patient_id == $scope.user_id || ($scope.active_user.hasOwnProperty('roel') && $scope.active_user.role != 'patient')) {
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

        // Initialize data for this page

        sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
            $scope.document = resp.data.info;
            $scope.todos_ready = true; // Should be removed
        });


        sharedService.getUploadedDocument().then(function (response) {
            $scope.uploadedDocuments  = response.data.documents;
        });


        patientService.fetchActiveUser().then(function (data) {
            // Logged in user profile in Django authentication system
            $scope.active_user = data['user_profile'];
        });
    }


})();