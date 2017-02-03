(function () {
    "use strict";
    angular.module('StaffApp')
        .controller('SettingPageController', SettingPageController);

    SettingPageController.$inject = ['$scope', 'staffService', 'sharedService'];

    function SettingPageController($scope, staffService, sharedService) {
        $scope.user = {};
        $scope.generalSettings = {};
        $scope.roles = [
            {slug: 'patient', display: 'Patient'},
            {slug: 'physician', display: 'Physician'},
            {slug: 'mid-level', display: 'Mid Level PA/NP'},
            {slug: 'nurse', display: 'Nurse'},
            {slug: 'secretary', display: 'Secretary'},
            {slug: 'admin', display: 'Admin'}
        ];

        $scope.updateSetting = updateSetting;

        init();

        function init() {
            staffService.fetchActiveUser($('#user_id').val())
                .then(function (data) {
                    $scope.user = data;
                });

            sharedService.getSettings().then(function (response) {
                angular.forEach( response.data.settings, function (value, key) {
                    $scope.generalSettings[key] = JSON.parse(value);
                });
            });
        }

        function updateSetting(key) {
            sharedService.updateSettings({
                setting_key: key,
                setting_value: JSON.stringify($scope.generalSettings[key])
            });
        }
    }
})();