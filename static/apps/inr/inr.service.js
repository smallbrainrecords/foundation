(function () {

    'use strict';

    angular.module('inr')
        .service('inrService', inrService);

    inrService.$inject = ['$http', '$q', '$cookies', 'httpService'];

    function inrService($http, $q, $cookies, httpService) {
        return {
            getINRTarget: getINRTarget,
            getINRs: getINRs,
            setINRTarget: setINRTarget,
            addINR: addINR,
            updateINR: updateINR,
            deleteINR: deleteINR,
            getProblems: getProblems,
            getMedications: getMedications,
            getOrders: getOrders,
            addOrder: addOrder,
            addNote: addNote,
            loadNotes: loadNotes,
            findPatient: findPatient
        };


        /**
         *  Get patient's goal range for INR value.
         *  Each patient can have one instance of this widget (which could be displayed in more than one problem).
         *  And each patient will have only one goal range for their inr value.
         *
         * @param patientId
         */
        function getINRTarget(patientId) {
            return $http.get(`/inr/${patientId}/target/get`);
        }

        /**
         * Loading data for INR tables
         * @param patientId
         * @param numberOfRow
         */
        function getINRs(patientId, numberOfRow) {
            return $http.post(`/inr/${patientId}/inrs/`, {
                row: numberOfRow
            });
        }

        /**
         * Set patient's goal range for INR value.
         * @param patientId
         * @param inr
         */
        function setINRTarget(patientId, inr) {
            return $http.post(`/inr/${patientId}/target/set`, {
                value: inr
            });
        }

        /**
         * Adding new INR to INR table, also add new data point to observation data point
         * @param patientId
         * @param inrObj
         */
        function addINR(patientId, inrObj) {
            return $http.post(`/inr/${patientId}/inr/add`, inrObj);
        }

        /**
         * Update an INR row in INR table
         * @param patientId
         * @param inrObj
         */
        function updateINR(patientId, inrObj) {
            return $http.post(`/inr/${patientId}/inr/update`, inrObj);
        }

        /**
         * Delete an INR object in INR table
         * @param patientId
         * @param inrObj
         */
        function deleteINR(patientId, inrObj) {
            return $http.post(`/inr/${patientId}/inr/delete`, inrObj);
        }

        /**
         *
         * @param patientId
         */
        function getProblems(patientId) {
            return $http.get(`/inr/${patientId}/problems`);
        }

        /**
         * Get all medication which have conceptID in this sets
         * {375383004, 375379004, 375378007, 319735007, 375374009, 319734006, 375380001, 375375005, 319733000, 319736008}
         * Refer: https://trello.com/c/Cts0FOSj
         *
         * @param patientId
         */
        function getMedications(patientId) {
            return $http.get(`/inr/${patientId}/medications`);
        }

        /**
         * Get all order related(generated) to this INR widget
         * Should be filtered by problem
         * @param patientId
         * @param problemId
         */
        function getOrders(patientId, problemId) {
            return $http.get(`/inr/${patientId}/${problemId}/orders`);
        }

        /**
         *
         * @param patientId
         * @param orderObj
         */
        function addOrder(patientId, orderObj) {
            return $http.post(`/inr/${patientId}/order/add`, orderObj);
        }

        /**
         *
         * @param patientId
         * @param noteObj
         */
        function addNote(patientId, noteObj) {
            return $http.post(`/inr/${patientId}/note/add`, noteObj);
        }

        /**
         *
         * @param patientId
         * @param numberOfRow
         */
        function loadNotes(patientId, numberOfRow) {
            return $http.post(`/inr/${patientId}/notes/`, {
                row: numberOfRow
            });
        }

        /**
         *
         * @param viewValue
         */
        function findPatient(viewValue) {
            return $http.post(`/inr/patients`, {
                search_str: viewValue
            });
        }
    }
})();