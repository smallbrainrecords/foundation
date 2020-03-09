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

    'use strict';


    angular.module('ManagerApp')
        .controller('PortraitUpdCtrl', ['$scope', 'patientService', 'toaster', function ($scope, patientService, toaster) {
            // METHOD 1: User select an image from their computer
            /**
             * Handler when user select file from computer
             * @param file
             */
            $scope.file_changed = function (file) {
                let reader = new FileReader();
                reader.addEventListener("load", function () {
                    $scope.preview_image_src = reader.result;
                    $scope.photo_is_taken_flag = false;
                    $scope.get_image_via_camera_flag = false;
                    $scope.files = {
                        portrait_image: file[0]
                    };
                    $scope.$apply();
                }, false);

                if (file[0]) {
                    reader.readAsDataURL(file[0]);
                }
            };

            // METHOD 2: User select take an image from integrate camera
            $scope.photo_is_taken_flag = false;
            $scope.get_image_via_camera_flag = false;
            let _video = null;
            $scope.channel = {};
            $scope.patOpts = {x: 0, y: 0, w: 25, h: 25};

            /**
             *
             */
            $scope.reset_take_photo_flags = function () {
                $scope.photo_is_taken_flag = false;
                $scope.get_image_via_camera_flag = true;
                $scope.preview_image_src = null;
            };

            /**
             * Get video data
             * @param x
             * @param y
             * @param w
             * @param h
             * @returns {ImageData}
             */
            $scope.getVideoData = function (x, y, w, h) {
                let hiddenCanvas = document.createElement('canvas');
                hiddenCanvas.width = _video.width;
                hiddenCanvas.height = _video.height;
                let ctx = hiddenCanvas.getContext('2d');
                ctx.drawImage(_video, 0, 0, _video.width, _video.height);
                return ctx.getImageData(x, y, w, h);
            };

            /**
             * Callback if there is any error when getting user camera access
             * @param err
             */
            $scope.onError = function (err) {
                $scope.$apply(function () {
                        $scope.webcamError = err;
                    }
                );
            };

            /**
             * Callback when success initialize camera
             */
            $scope.onSuccess = function () {
                // The video element contains the captured camera data
                _video = $scope.channel.video;
                $scope.$apply(function () {
                    $scope.patOpts.w = _video.width;
                    $scope.patOpts.h = _video.height;
                    $scope.showDemos = true;
                });
            };

            $scope.dataURItoFile = function (dataURI) {
                // convert base64/URLEncoded data component to raw binary data held in a string
                let byteString;
                if (dataURI.split(',')[0].indexOf('base64') >= 0)
                    byteString = atob(dataURI.split(',')[1]);
                else
                    byteString = unescape(dataURI.split(',')[1]);

                // separate out the mime component
                let mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];

                // write the bytes of the string to a typed array
                let ia = new Uint8Array(byteString.length);
                for (var i = 0; i < byteString.length; i++) {
                    ia[i] = byteString.charCodeAt(i);
                }
                let blob = new Blob([ia], {type: mimeString});
                return new File([blob], (new Date()).getTime() + ".png");
            };

            /**
             * Take a snap shot from video
             * Close camera preview
             * Set image preview
             */
            $scope.take_snapshot = function () {
                if (_video) {
                    // Flag to determine photo is taken or not
                    $scope.get_image_via_camera_flag = false;
                    $scope.photo_is_taken_flag = true;
                    let patCanvas = document.querySelector('#snapshot');
                    if (!patCanvas) return;

                    patCanvas.width = _video.width;
                    patCanvas.height = _video.height;
                    let ctxPat = patCanvas.getContext('2d');
                    let idata = $scope.getVideoData($scope.patOpts.x, $scope.patOpts.y, $scope.patOpts.w, $scope.patOpts.h);
                    ctxPat.putImageData(idata, 0, 0);

                    $scope.preview_image_src = patCanvas.toDataURL();
                    $scope.files = {
                        portrait_image: $scope.dataURItoFile(patCanvas.toDataURL())
                    }
                }
            };


            /**
             * Close the form
             * Upload selected file to server then replace
             */
            $scope.submit_form = function () {
                let form = {};
                form.user_id = $scope.patient_info.user.id;
                form.phone_number = $scope.patient_info.phone_number;
                form.sex = $scope.patient_info.sex;
                form.role = $scope.patient_info.role;
                form.summary = $scope.patient_info.summary;
                form.date_of_birth = $scope.patient_info.date_of_birth;

                let files = $scope.files;

                patientService.updateProfile(form, files).then(function (data) {
                    if (data['success']) {
                        $scope.$emit('portrait_image_updated', {data: data['info']});
                        $scope.closeThisDialog();
                    }
                });
            };
        }]);
})();