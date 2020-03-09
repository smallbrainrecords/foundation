/*
 * Copyright (c) Small Brain Records 2014-2020. Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
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
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */
/*
 * Allow easy to modify user cover image and profile image
 * - Change profile images by take image from webcam
 * - Change profile image by pick computer image
 * - Remove cover image
 * - Change cover image by pick computer image
 * - After image being selected it'll be taking effect immediately
 */
(function () {
    "use strict";

    angular.module('app.components')
        .component('patientProfilePicture', {
            bindings: {
                profile: '<',
                onUpdate: '&'
            },
            templateUrl: "/static/apps/common/components/patient-profile-picture/patient-profile-picture.html",
            controller: userProfilePictureController
        });

    /**
     * Inject dependencies
     * @type {[*]}
     */
    userProfilePictureController.$inject = ['ngDialog', 'patientService'];


    /**
     * Reusable medication search box Add new or update existing(depend on update callback)
     * Input: Initial search string (default: empty)
     * Output: Update or Create callback
     *
     */
    function userProfilePictureController(ngDialog, patientService) {
        // Temporary solution for this (controllerAs syntax)
        let ctrl = this;

        // Properties

        // Behaviors
        ctrl.onCoverPictureUpload = onCoverPictureUpload;
        ctrl.onCoverPictureRemove = onCoverPictureRemove;
        ctrl.updateProfilePicture = updateProfilePicture;

        ctrl.$onInit = function () {
        };

        /**
         * Callback when user choose new cover image from computer
         * Do both upload image and update profile object
         */
        function onCoverPictureUpload(file) {
            if (!file) {
                return;
            }

            patientService.updateCoverImage(ctrl.profile.id, file);
        }

        function onCoverPictureRemove() {
            // Save to persistence
            patientService.removeCoverImage(ctrl.profile.id).then((response) => {
                delete ctrl.profile.cover_image;
            });
        }

        function updateProfilePicture() {
            ngDialog.open({
                controller: 'PortraitUpdCtrl',
                template: 'portraitUpdateDialog'
            });
        }
    }
})();