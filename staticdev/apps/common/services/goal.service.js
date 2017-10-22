(function(){

	'use strict';

    angular.module('app.services').service('goalService', function ($http, $q, $cookies, httpService) {
        return {
            updateGoalStatus: updateGoalStatus,
            addNote: addNote,
            changeGoalName: changeGoalName
        };

        function updateGoalStatus(form) {

            let url = `/g/patient/${form.patient_id}/goal/${form.goal_id}/update_status`;
            return httpService.post(form, url);

        }

        function addNote(form) {

            let url = `/g/patient/${form.patient_id}/goal/${form.goal_id}/add_note`;
			return httpService.post(form, url);


        }

        function changeGoalName(form) {
            let url = `/g/patient/${form.patient_id}/goal/${form.goal_id}/change_name`;
			return httpService.post(form, url);
        }
    });

})();