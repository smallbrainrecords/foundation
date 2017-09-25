(function () {

    'use strict';


    angular.module('ManagerApp')
        .controller('GoalsCtrl', function ($scope, $routeParams, patientService, ngDialog, toaster, goalService, sharedService) {


            var patient_id = $('#patient_id').val();

            var goal_id = $routeParams.goal_id;

            $scope.goal_id = goal_id;
            $scope.patient_id = patient_id;

            $scope.loading = true;

            $scope.edit_goal = false;
            $scope.new_goal_name = null;

            //sharedService.initHotkey($scope);

            patientService.fetchActiveUser().then(function (data) {

                $scope.active_user = data['user_profile'];

            });


            patientService.fetchGoalInfo(goal_id).then(function (data) {

                $scope.goal = data['goal'];
                $scope.goal_notes = data['goal_notes'];
                $scope.loading = false;

            });


            /* Track goal status */

            $scope.$watch('[goal.is_controlled,goal.accomplished]', function (newVal, oldVal) {

                if ($scope.loading == true) {
                    return false;
                }

                if (angular.equals(oldVal, [undefined, undefined])) {
                    return false;
                }

                var form = {};
                form.patient_id = $scope.patient_id;
                form.goal_id = $scope.goal_id;
                form.is_controlled = $scope.goal.is_controlled;
                form.accomplished = $scope.goal.accomplished;

                goalService.updateGoalStatus(form).then(function (data) {

                    toaster.pop('success', 'Done', 'Updated Goal Status');

                });


            });


            $scope.update_motivation = function () {

                var form = {};
                form.patient_id = $scope.patient_id;
                form.goal_id = $scope.goal_id;

                form.new_note = $scope.new_note;

                goalService.addNote(form).then(function (data) {

                    $scope.goal_notes.unshift(data['note']);

                    toaster.pop('success', 'Done', 'Added Note');
                })


            };

            $scope.edit_goal_name = function () {
                $scope.edit_goal = true;
                $scope.new_goal_name = $scope.goal.goal;
            };

            $scope.cancel_goal_name = function () {
                $scope.edit_goal = false;
            };

            $scope.change_goal_name = function (new_goal_name) {
                if (new_goal_name == '' || new_goal_name == undefined) {
                    return false;
                }

                var form = {};
                form.goal = new_goal_name;
                form.patient_id = $scope.patient_id;
                form.goal_id = $scope.goal_id;

                goalService.changeGoalName(form).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', 'Done', 'Goal name changed successfully');
                        $scope.goal = data['goal'];
                        $scope.edit_goal = false;
                    } else if (data['success'] == false) {
                        toaster.pop('error', 'Error', data['msg']);
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong');
                    }
                });
            };


            $scope.permitted = function (permissions) {

                if ($scope.active_user == undefined) {
                    return false;
                }
                var user_permissions = $scope.active_user.permissions;
                for (var key in permissions) {
                    if (user_permissions.indexOf(permissions[key]) < 0) {
                        return false;
                    }
                }
                return true;
            };


        });
    /* End of controller */


})();