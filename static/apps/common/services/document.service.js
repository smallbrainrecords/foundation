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

    angular.module('app.services')
        .config(function ($routeProvider, $httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        })
        .run(function run($http, $cookies) {
            $http.defaults.headers.common["X-CSRFToken"] = $cookies.get('csrftoken')
        })
        .service('documentService', function ($http, $q, $cookies, Upload) {
            return {
                csrf_token: csrf_token,
                uploadDocument: uploadDocument,
                getUploadedDocument: getUploadedDocument,
                getDocumentInfo: getDocumentInfo,
                pinPatient2Document: pinPatient2Document,
                pinTodo2Document: pinTodo2Document,
                pinProblem2Document: pinProblem2Document,
                updateDocumentName: updateDocumentName
            };

            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            /**
             * WIP
             * Upload one or multiple documentation
             * @param files
             * @param logs
             * @param author
             */
            function uploadDocument(files, logs, author) {
                if (files && files.length) {
                    for (let i = 0; i < files.length; i++) {
                        logs[i] = {
                            status: '',
                            progress: 0,
                            documentId: null
                        };
                        let file = files[i];
                        if (!file.$error) {
                            Upload.upload({
                                url: '/docs/upload_document',
                                data: {
                                    author: author,     // File owner
                                    file: file,         // File itself
                                    fileId: i           // Using to reference progress and upload status
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

            }
            /**
             * Get list of document user have uploaded
             */
            function getUploadedDocument(params) {
                return $http.get('/docs', {
                    params: params
                });
            }
            /**
             * @param documentId
             */
            function getDocumentInfo(documentId) {
                return $http.get('/docs/info/' + documentId);
            }
            /**
             *
             * Pin any patient to a document
             * @param document
             * @param patient
             * @returns {HttpPromise}
             */
            function pinPatient2Document(document, patient) {
                return $http.post('/docs/pin/patient', {
                    document: document.id,
                    patient: patient.uid
                }, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            }
            /**
             * Pin any active todo to a document
             * @param document
             * @param todo
             * @returns {HttpPromise}
             */
            function pinTodo2Document(document, todo) {
                return $http.post('/docs/pin/todo', {
                    document: document.id,
                    todo: todo.id
                }, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            }
            /**
             * Pin any problem to a document
             * @param document
             * @param problem
             * @returns {HttpPromise}
             */
            function pinProblem2Document(document, problem) {
                return $http.post('/docs/pin/problem', {
                    document: document.id,
                    problem: problem.id
                }, {
                    headers: {
                        'X-CSRFToken': $cookies.get('csrftoken')
                    }
                });
            }

            function updateDocumentName(documentId, formObj) {
                return $http.patch('/docs/' + documentId + '/name', formObj);
            }
        });
})();