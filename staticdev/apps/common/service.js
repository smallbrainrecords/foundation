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
                                'X-CSRFToken': $cookies.get('csrftoken')
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

        /**
         *
         * @param document      Id of document will be delete
         * @param tag_id        Id of tag item will be deleted
         * @param tag_type      Type of tagging document 'problem' or 'todo'
         * @param del_in_sys    Flag indicate will file be deleted in system or not
         */
        this.deleteDocumentTag = function (document, tag_id, tag_type, del_in_sys) {
            del_in_sys = del_in_sys == undefined ? false : del_in_sys;
            return $http.post('/docs/delete/' + document.id, {
                'document': document.id,
                'del_tag_id': tag_id.id,
                'del_tag_type': tag_type,
                'del_in_sys': del_in_sys
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            })
        }
    }
})();
