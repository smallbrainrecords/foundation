/*
 * Copyright (c) Small Brain Records 2014-2020. Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
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
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */

(function () {
    'use strict';

    angular.module('app.directives')
        .directive('sbClickTrack', sbClickTrack);

    sbClickTrack.$inject = ['medicationService'];

    /**
     * Currently supported click tracking for medication only.
     * Need to think a way to general tracking other function with other services.
     * @param medicationService
     * @returns {{link: fnLink, restrict: string}}
     */
    function sbClickTrack(medicationService) {
        return {
            restrict: 'A',
            link: fnLink
        };

        function fnLink($scope, $element, $attrs) {
            let patientId = $scope.medication.patient.id;
            let medicationId = $scope.medication.id;
            $element.click(() => {
                console.info(`DOM_CLICKED`);
                medicationService.trackMedication(patientId, medicationId)
            });
        }
    }
})();