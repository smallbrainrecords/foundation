(function () {

    'use strict';

    angular.module('inr')
        .service('inrService', inrService);

    inrService.$inject = ['$http', '$q', '$cookies', 'httpService'];

    function inrService($http, $q, $cookies, httpService) {
        this.csrf_token = function () {
            return $cookies.get('csrftoken');
        };

        /**
         *  Get patient's goal range for INR value.
         *  Each patient can have one instance of this widget (which could be displayed in more than one problem).
         *  And each patient will have only one goal range for their inr value.
         *
         * @param patientId
         */
        this.getINRTarget = function (patientId) {
            return $http.get('/inr/' + patientId + '/target/get');
        };

        /**
         * Loading data for INR tables
         * @param patientId
         * @param numberOfRow
         */
        this.getINRs = function (patientId, numberOfRow) {
            return $http.get('/inr/' + patientId + '/inrs/', {
                row: numberOfRow
            });
        };

        /**
         * Set patient's goal range for INR value.
         * @param patientId
         * @param inr
         */
        this.setINRTarget = function (patientId, inr) {
            return $http.post('/inr/' + patientId + '/target/set', {
                value: inr
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         * Adding new INR to INR table, also add new data point to observation data point
         * @param patientId
         * @param inrObj
         */
        this.addINR = function (patientId, inrObj) {
            return $http.post('/inr/' + patientId + '/add', inrObj, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };


        /**
         * Update an INR row in INR table
         * @param patientId
         * @param inrObj
         */
        this.updateINR = function (patientId, inrObj) {
            return $http.post('/inr/' + patientId + '/update', inrObj, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         * Delete an INR object in INR table
         * @param patientId
         * @param inrObj
         */
        this.deleteINR = function (patientId, inrObj) {
            return $http.post('/inr/' + patientId + '/delete', inrObj, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };


        /**
         *
         * @param patientId
         */
        this.getProblems = function (patientId) {
            return $http.get('/inr/' + patientId + '/problems');
        };

        /**
         * Get all medication which have conceptID in this sets
         * {375383004, 375379004, 375378007, 319735007, 375374009, 319734006, 375380001, 375375005, 319733000, 319736008}
         * Refer: https://trello.com/c/Cts0FOSj
         *
         * @param patientId
         */
        this.getMedications = function (patientId) {
            return $http.get('/inr/' + patientId + '/medications');
        };

        /**
         * Get all order related(generated) to this INR widget
         * @param patientId
         */
        this.getOrders = function (patientId) {
            return $http.get('/inr/' + patientId + '/orders');
        };

        /**
         *
         * @param patientId
         * @param orderObj
         */
        this.addOrder = function (patientId, orderObj) {
            return $http.post('/inr/' + patientId + '/orders/add', orderObj, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         *
         * @param patientId
         * @param noteObj
         */
        this.addNote = function (patientId, noteObj) {
            return $http.post('/inr/' + patientId + '/note/add', noteObj, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };

        /**
         *
         * @param patientId
         * @param numberOfRow
         */
        this.loadNotes = function (patientId, numberOfRow) {
            return $http.post('/inr/' + patientId + '/notes/', {
                row: numberOfRow
            }, {
                headers: {
                    'X-CSRFToken': $cookies.get('csrftoken')
                }
            });
        };
    }
})();