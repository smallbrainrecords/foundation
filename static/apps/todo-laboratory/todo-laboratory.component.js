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
    "use strict";

    angular.module('ManagerApp')
        .component('todoLaboratory', {
            templateUrl: "/static/apps/todo-laboratory/todo-laboratory.template.html",
            controller: todoLaboratoryController
        });

    /**
     *
     * @type {string[]}
     */
    todoLaboratoryController.$inject = ['patientService'];

    /**
     *
     */
    function todoLaboratoryController(patientService) {
        // Temporary solution for this (controllerAs syntax)
        let ctrl = this;
        ctrl.todoLabels = [];
        ctrl.activeTodos = [];
        ctrl.doPrint = doPrint;

        ctrl.$onInit = () => {
            console.log('On component initialisation');
            patientService.getToDo(4, false, true, 1).then((resp) => {
                if (resp.success) {
                    ctrl.activeTodos = resp.data;
                }
            });
        };

        /**
         *
         */
        function doPrint() {

        }
    }
})();