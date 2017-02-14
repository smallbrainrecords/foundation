(function () {

    'use strict';
    /**
     * Implement encounter recorder fail safe recovery
     *
     */
    angular.module('ManagerApp')
        .service('encounterRecorderFailSafeService', function () {

            /**
             * Create new blob arrays or recover from last unsaved session
             * @returns {Blob}
             */
            this.restoreUnsavedBlob = function () {
                // Get last store session
                var cached = localStorage.getItem('cached-data');
                if (cached !== null) {
                    return this.dataURItoBlob(cached);
                }
            };


            /**
             * Restore total time recorded
             * @returns {number}
             * @deprecated
             */
            this.restoreUnsavedDuration = function () {
                var duration = localStorage.getItem('cached-duration');
                return duration == null ? 0 : duration;
            };

            /**
             * Store the blob to localStorage as base64string
             * Store data
             * Store information last duration also
             * @param blob         Array of blob storages
             * @param duration    Total duration recorded in this encounter session
             */
            this.storeBlob = function (blob, duration) {
                var reader = new window.FileReader();
                reader.readAsDataURL(blob);
                reader.onloadend = function () {
                    var base64data = reader.result;
                    localStorage.setItem('cached-data', base64data);
                };

                //
                localStorage.setItem('cached-duration', duration);
            };


            /**
             * Convert base64string to mp3 blob file
             * @param dataURI
             * @param callback
             * @returns {Blob}
             */
            this.dataURItoBlob = function (dataURI, callback) {
                // convert base64 to raw binary data held in a string
                // doesn't handle URLEncoded DataURIs - see SO answer #6850276 for code that does this
                var byteString = atob(dataURI.split(',')[1]);

                // separate out the mime component
                var mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0]

                // write the bytes of the string to an ArrayBuffer
                var ab = new ArrayBuffer(byteString.length);
                var ia = new Uint8Array(ab);
                for (var i = 0; i < byteString.length; i++) {
                    ia[i] = byteString.charCodeAt(i);
                }

                // write the ArrayBuffer to a blob, and you're done
                return new Blob([ab]);
            };

              /**
             * Remove last stored session
             */
            this.clearUnsavedData = function () {
                localStorage.removeItem('cached-data');
                localStorage.removeItem('cached-duration');
            };
        });
})();