(function () {
    'use strict';
    angular.module('AdminApp')
        .controller('HomeCtrl', function ($scope, $routeParams, ngDialog, adminService, sharedService) {
            $scope.refresh_pending_users = refresh_pending_users;
            $scope.updatePendingUser = updatePendingUser;
            init();
            function init() {
                $scope.users = [];
                adminService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                    var role_form = {
                        'actor_role': $scope.active_user.role,
                        'actor_id': $scope.active_user.user.id
                    };
                    adminService.getUsersList(role_form).then(function (data) {
                        $scope.users = data;
                    });
                    adminService.getPendingRegistrationUsersList(role_form).then(function (data) {
                        $scope.pending_users = data;
                    });
                    if ($scope.active_user.role == 'physician') {
                        var form = {'physician_id': $scope.active_user.user.id};
                        adminService.getPhysicianData(form).then(function (data) {
                            $scope.patients = data['patients'];
                            $scope.team = data['team'];
                        });
                    }
                });
            }

            function refresh_pending_users() {
                adminService.getPendingRegistrationUsersList().then(function (data) {
                    $scope.pending_users = data;
                });
            }

            function updatePendingUser(user, status) {
                switch (status) {
                    case 1: // Approve
                        if (user.role == 'patient' || user.role == 'physician' || user.role == 'admin') {
                            sharedService.approveUser(user).then(userUpdateSucceed);
                        } else {
                            alert("Please assign role!");
                        }
                        break;
                    case 0: // Reject
                        sharedService.rejectUser(user).then(userUpdateSucceed);
                        break;
                }

                function userUpdateSucceed() {
                    let index = $scope.pendingUsers.indexOf(user);
                    if (index > -1) {
                        $scope.pendingUsers.splice(index, 1);
                    }
                }
            }
        });
    /* End of controller */
})();