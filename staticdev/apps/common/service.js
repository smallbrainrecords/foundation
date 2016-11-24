(function () {

    'use strict';
    angular.module('sharedModule', ['ngFileUpload'])
        .service('sharedService', sharedService);

    sharedService.$inject = ['$http', '$cookies', 'Upload'];


    function sharedService($http, $cookies, Upload) {
        /**
         * Upload multiple documentation
         * @param files
         * @param author
         * @param patient
         * @param callback
         */
        this.uploadDocument = function (files, author, patient, callback) {
            if (files && files.length) {
                for (var i = 0; i < files.length; i++) {
                    var file = files[i];
                    if (!file.$error) {
                        Upload.upload({
                            url: '/docs/upload_document',
                            data: {
                                author: author,     // File owner
                                patient: patient,   // Primary pinned patient
                                file: file          // File itself
                            },
                            headers: {
                                'X-CSRFToken': $cookies.csrftoken
                            }
                        }).then(function (resp) {
                            callback(resp);
                        }, function (resp) {
                        }, function (evt) {
                        });
                    }
                }
            }
        };
    }
})();
