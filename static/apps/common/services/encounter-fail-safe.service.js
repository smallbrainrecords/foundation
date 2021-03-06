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
    /**
     * Implement encounter recorder fail safe recovery
     *
     */
    angular.module('app.services')
        .service('encounterRecorderFailSafeService', function ($indexedDB) {
            return {
                restoreUnsavedBlob: restoreUnsavedBlob,
                restoreUnsavedDuration: restoreUnsavedDuration,
                storeBlob: storeBlob,
                dataURItoBlob: dataURItoBlob,
                clearUnsavedData: clearUnsavedData,
            };

            /**
             * Create new blob arrays or recover from last unsaved session
             * @param patientID
             * @returns {Blob}
             */
            function restoreUnsavedBlob(patientID) {
                $indexedDB.openStore("encounter", (store) => {
                    store.find(patientID).then((e) => {
                        return this.dataURItoBlob(e.audio);
                    })
                });
            }

            /**
             * Restore total time recorded
             * @returns {number}
             */
            function restoreUnsavedDuration() {
                let duration = localStorage.getItem('cached-duration');
                return _.isNull(duration) ? 0 : duration;
            }

            /**
             * Store the blob to localStorage as base64string
             * Store data
             * Store information last duration also
             * @param patientID
             * @param blob         Array of blob storages
             * @param duration    Total duration recorded in this encounter session
             */
            function storeBlob(patientID, blob, duration) {
                let reader = new window.FileReader();
                reader.readAsDataURL(blob);
                reader.onloadend = function () {
                    let base64data = reader.result;
                    $indexedDB.openStore('encounter', function (store) {
                        store.insert({"id": patientID, "audio": base64data}).then((e) => {
                        }, (e) => {
                            console.log(e);
                        });
                    });
                };

                localStorage.setItem('cached-duration', duration);
            }

            /**
             * Convert base64string to mp3 blob file
             * @param dataURI
             * @param callback
             * @returns {Blob}
             */
            function dataURItoBlob(dataURI, callback) {
                // convert base64 to raw binary data held in a string
                // doesn't handle URLEncoded DataURIs - see SO answer #6850276 for code that does this
                var byteString = atob(dataURI.split(',')[1]);

                // separate out the mime component
                var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];

                // write the bytes of the string to an ArrayBuffer
                var ab = new ArrayBuffer(byteString.length);
                var ia = new Uint8Array(ab);
                for (var i = 0; i < byteString.length; i++) {
                    ia[i] = byteString.charCodeAt(i);
                }

                // write the ArrayBuffer to a blob, and you're done
                return new Blob([ab]);
            }

            /**
             * Remove last stored session
             */
            function clearUnsavedData(patientID, authorID) {
                // localStorage.removeItem('cached-data');
                $indexedDB.openStore("encounter", (store) => {
                    store.delete(patientID);
                });
                localStorage.removeItem('cached-duration');
            }
        });
})();