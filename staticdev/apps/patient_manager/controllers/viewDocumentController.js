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
     * @constructor
     */
    function ViewDocumentCtrl($scope, sharedService, $routeParams, patientService, $location, toaster) {

        sharedService.getDocumentInfo($routeParams.documentId).then(function (resp) {
            $scope.document = resp.data.info;
            $scope.todos_ready = true; // Should be removed
        });

        $scope.open_problem = function (problem) {
            $location.path('/problem/' + problem.id);
        };


        patientService.fetchActiveUser().then(function (data) {
            // Logged in user profile in Django authentication system
            $scope.active_user = data['user_profile'];
        });

        // Patients are being managed
        var patient_id = $('#patient_id').val();
        // Patients are being managed
        $scope.patient_id = patient_id;

        // Current logged in id
        var user_id = $('#user_id').val();
        // Current logged in id
        $scope.user_id = user_id;

        $scope.checkSharedProblem = function (problem, sharing_patients) {
            if ($scope.patient_id == $scope.user_id || $scope.active_user.role != 'patient') {
                return true;
            } else {
                var is_existed = false;
                angular.forEach(sharing_patients, function (p, key) {
                    if (!is_existed && p.user.id == $scope.user_id) {
                        is_existed = $scope.isInArray(p.problems, problem.id);
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
        }
    }


})();