/**
 * Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */
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