(function () {

    'use strict';

    angular.module('document', ['ngFileUpload'])
        .run(function run($http, $cookies) {
            $http.defaults.headers.common["X-CSRFToken"] = $cookies.get('csrftoken')
        })
        .service('documentService', function ($http, $q, $cookies, Upload) {

            this.csrf_token = function () {
                return $cookies.get('csrftoken');
            };

            /**
             * WIP
             * Upload one or multiple documentation
             * @param files
             * @param logs
             */
            this.uploadDocument = function (files, logs, author) {
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
                                url: '/docs/upload_document',
                                data: {
                                    author: author,    // File owner
                                    file: file,  // File itself
                                    fileId: i  // using to reference progress and upload status
                                },
                                headers: {
                                    'X-CSRFToken': $cookies.get('csrftoken')
                                }
                            }).then(function (resp) {
                                logs[resp.config.data.fileId].status = "Upload success";
                                logs[resp.config.data.fileId].document = resp.data.document;
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
             * Get list of document user have uploaded
             */
            this.getUploadedDocument = function () {
                return $http.get('/docs/list');
            };

            /**
             * @param documentId
             */
            this.getDocumentInfo = function (documentId) {
                return $http.get('/docs/info/' + documentId);
            };


            /**
             *
             * Pin any patient to a document
             * @param document
             * @param patient
             * @returns {HttpPromise}
             */
            this.pinPatient2Document = function (document, patient) {
                return $http.post('/docs/pin/patient', {
                    document: document.id,
                    patient: patient.uid
                }, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            };

            /**
             * Pin any active todo to a document
             * @param document
             * @param todo
             * @returns {HttpPromise}
             */
            this.pinTodo2Document = function (document, todo) {
                return $http.post('/docs/pin/todo', {
                    document: document.id,
                    todo: todo.id
                }, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            };

            /**
             * Pin any problem to a document
             * @param document
             * @param problem
             * @returns {HttpPromise}
             */
            this.pinProblem2Document = function (document, problem) {
                return $http.post('/docs/pin/problem', {
                    document: document.id,
                    problem: problem.id
                }, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            };


            this.updateDocumentName = function (documentId, formObj) {
                return $http.patch('/docs/' + documentId + '/name', formObj);
            };
        });
})();