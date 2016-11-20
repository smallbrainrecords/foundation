(function () {

    'use strict';

    angular.module('StaffApp')
        .service('documentService', function ($http, $q, $cookies, Upload) {

            this.csrf_token = function () {
                return $cookies.csrftoken;
            };

            /**
             * WIP
             * Upload one or multiple documentation
             * @param files
             * @param logs
             */
            this.uploadDocument = function (files, logs) {
                if (files && files.length) {
                    for (var i = 0; i < files.length; i++) {
                        logs[i] = {
                            status: '',
                            progress: 0,
                            documentId: null
                        };
                        var file = files[i];
                        if (!file.$error) {
                            Upload.upload({
                                url: 'https://angular-file-upload-cors-srv.appspot.com/upload', // TODO: Update endpoint
                                data: {
                                    uid: 10,    // File owner
                                    fileId: i,  // using to reference progress and upload status
                                    file: file  // File itsefl
                                }
                            }).then(function (resp) {
                                logs[resp.config.data.fileId].status = "Upload success";
                                logs[resp.config.data.fileId].documentId = resp.config.data.documentId;
                            }, function (resp) {
                                logs[resp.config.data.fileId].status = "Upload failed";
                            }, function (evt) {
                                logs[evt.config.data.fileId].progress = parseInt(100.0 *
                                    evt.loaded / evt.total);
                            });
                        }
                    }
                }

            };


            /**
             * WIP
             * Get list of document user have uploaded
             */
            this.getUploadedDocument = function () {
                return [{
                    id: 1,
                    name: 'abcxyz.docs'
                }, {
                    id: 2,
                    name: 'abcxyz.pdf'
                }]
            };


            this.pinPatient2Document = function () {

            };
        });

})();