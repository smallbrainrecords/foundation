(function () {

    'use strict';

    angular.module('ManagerApp').service('inrService',
        function ($http, $q, $cookies, httpService) {
            return {
                csrf_token: csrf_token,
                getInrs: getInrs,
                setTargetforInr: setTargetforInr,
                getListProblem: getListProblem,
                saveInrValue: saveInrValue,
                editInrValue: editInrValue,
                deleteInrValue: deleteInrValue,
                addNote: addNote
            };

            function csrf_token() {
                return $cookies.get('csrftoken');
            }

            function getInrs(patient_id, problem_id) {
                let params = {};
                let url = `/inr/${patient_id}/${problem_id}/get_inrs`;
                return httpService.get(params, url);
            }

            function setTargetforInr(inr_id, target) {
                let params = {"target": target};
                let url = `/inr/${inr_id}/set_target`;
                return httpService.get(params, url);
            }

            function getListProblem(id) {
                let params = {"id": id};
                let url = '/inr/get_list_problem';
                return httpService.get(params, url);
            }

            function saveInrValue(datas) {
                let params = {"datas": datas};
                let url = '/inr/save_inrvalue';
                return httpService.post(datas, url);
            }

            function editInrValue(value, id) {
                let params = {"datas": value};
                let url = `/inr/${id}/edit_inrvalue`;
                return httpService.post(value, url);
            }

            function deleteInrValue(id) {
                let params = {};
                let url = `/inr/${id}/delete_inrvalue`;
                return httpService.get(params, url);
            }

            function addNote(note) {
                let url = '/inr/add_note';
                return httpService.post(note, url);
            }
        });

})();