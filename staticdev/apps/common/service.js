(function () {

    'use strict';

    angular.module('sharedModule', ['ngFileUpload', 'httpModule', 'cfp.hotkeys'])
        .service('sharedService', sharedService);

    sharedService.$inject = ['$http', '$cookies', 'Upload', 'hotkeys', '$location'];

    function sharedService($http, $cookies, Upload, hotkeys, $location) {
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
        };

        /**
         *
         * @param problem_id
         */
        this.getDocumentByProblem = function (problem_id) {
            return $http.get('/docs/problem/' + problem_id);
        };

        /**
         * Add a label to document
         * @param document
         * @param label
         */
        this.pinLabelToDocument = function (document, label) {
            return $http.post('/docs/pin/label', {
                document: document.id,
                label: label.id
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         * Remove a label in document
         * @param document
         * @param label
         */
        this.unpinDocumentLabel = function (document, label) {
            return $http.post('/docs/remove/label', {
                document: document.id,
                label: label.id
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         * Remove an pinned problem in document
         * @param document
         * @param problem
         */
        this.unpinDocumentProblem = function (document, problem) {
            return $http.post('/docs/unpin/problem', {
                document: document.id,
                problem: problem.id
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         * Remove an pinned todo in document
         * @param document
         * @param todo
         */
        this.unpinDocumentTodo = function (document, todo) {
            return $http.post('/docs/unpin/todo', {
                document: document.id,
                todo: todo.id
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         *
         * @param documentId
         */
        this.getDocumentInfo = function (documentId) {
            return $http.get('/docs/info/' + documentId);
        };


        /**
         *
         * @param document
         */
        this.removeDocument = function (document) {
            return $http.post('/docs/remove/' + document.id, null, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         * Get list of document user have uploaded
         */
        this.getUploadedDocument = function () {
            return $http.get('/docs/list');
        };

        this.getSettings = function () {
            return $http.get('/u/setting');
        };

        this.updateSettings = function (settingObj) {
            return $http.post('/u/update_setting', settingObj, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        }
    }
})();
