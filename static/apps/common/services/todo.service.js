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

    angular.module('app.services').service('todoService',
        function ($http, $q, $cookies, httpService) {
            return {
                csrf_token: csrf_token,
                fetchTodoInfo: fetchTodoInfo,
                addComment: addComment,
                editComment: editComment,
                deleteComment: deleteComment,
                changeTodoText: changeTodoText,
                changeTodoDueDate: changeTodoDueDate,
                addTodoLabel: addTodoLabel,
                removeTodoLabel: removeTodoLabel,
                saveCreateLabel: saveCreateLabel,
                saveEditLabel: saveEditLabel,
                deleteLabel: deleteLabel,
                addTodoAccessEncounter: addTodoAccessEncounter,
                addAttachment: addAttachment,
                deleteAttachment: deleteAttachment,
                getTodoActivity: getTodoActivity,
                fetchTodoMembers: fetchTodoMembers,
                addTodoMember: addTodoMember,
                removeTodoMember: removeTodoMember,
                fetchLabels: fetchLabels,
                updateTodoOrder: updateTodoOrder,
                updateTodoStatus: updateTodoStatus,
                saveTodoPrintLogs: saveTodoPrintLogs
            };

            function csrf_token() {

                return $cookies.get('csrftoken');
            }

            function fetchTodoInfo(todo_id) {
                let url = `/todo/todo/${todo_id}/info`;
                let params = {};

                return httpService.get(params, url);

            }

            function addComment(form) {
                let url = `/todo/todo/${form.todo_id}/comment`;

                return httpService.post(form, url);
            }

            function editComment(form) {
                let url = `/todo/todo/${form.id}/edit`;

                return httpService.post(form, url);
            }

            function deleteComment(form) {
                let url = `/todo/todo/${form.id}/delete`;

                return httpService.post(form, url);
            }

            function changeTodoText(form) {
                let url = `/todo/todo/${form.id}/changeText`;

                return httpService.post(form, url);
            }

            function changeTodoDueDate(form) {
                let url = `/todo/todo/${form.id}/changeDueDate`;

                return httpService.post(form, url);
            }

            function addTodoLabel(id, todo_id) {
                let form = {};
                let url = `/todo/todo/${id}/${todo_id}/addLabel`;

                return httpService.post(form, url);
            }

            function removeTodoLabel(id, todo_id) {
                let form = {};
                let url = `/todo/todo/removeLabel/${id}/${todo_id}`;

                return httpService.post(form, url);
            }

            function saveCreateLabel(todo_id, form) {
                let url = `/todo/todo/newLabel/${todo_id}`;

                return httpService.post(form, url);
            }

            function saveEditLabel(form) {
                let url = `/todo/todo/saveEditLabel/${form.id}`;

                return httpService.post(form, url);
            }

            function deleteLabel(form) {
                let url = `/todo/todo/deleteLabel/${form.id}`;

                return httpService.post(form, url);
            }

            function addTodoAccessEncounter(id) {
                let form = {};
                let url = `/todo/todo/accessEncounter/${id}`;

                return httpService.post(form, url);
            }

            function addAttachment(form, file) {
                let deferred = $q.defer();

                let uploadUrl = `/todo/todo/${form.todo_id}/addAttachment`;

                let fd = new FormData();

                fd.append('csrfmiddlewaretoken', this.csrf_token());

                fd.append(0, file);


                $http.post(uploadUrl, fd, {
                    transformRequest: angular.identity,
                    headers: {'Content-Type': undefined}
                }).then(function (data) {
                    deferred.resolve(data);
                }, function (data) {
                    deferred.resolve(data);

                });

                return deferred.promise;
            }

            function deleteAttachment(form) {
                let url = `/todo/attachment/${form.id}/delete`;

                return httpService.post(form, url);
            }

            function getTodoActivity(todo_id, last_id) {
                let params = {};
                let url = `/todo/todo/${todo_id}/${last_id}/activity/`;
                return httpService.get(params, url);
            }

            function fetchTodoMembers(user_id) {
                let params = {};
                let url = `/u/members/${user_id}/getlist/`;
                return httpService.get(params, url);
            }

            function addTodoMember(form, member) {
                let url = `/todo/todo/${form.id}/addMember`;

                return httpService.post(member, url);
            }

            function removeTodoMember(form, member) {
                let url = `/todo/todo/${form.id}/removeMember`;

                return httpService.post(member, url);
            }

            function fetchLabels(user_id) {
                let params = {};
                let url = `/todo/todo/${user_id}/getlabels`;
                return httpService.get(params, url);
            }

            function updateTodoOrder(form) {
                let url = '/todo/todo/updateOrder/';
                return httpService.postJson(form, url);
            }

            function updateTodoStatus(form) {
                let url = `/todo/todo/${form.id}/update/`;
                return httpService.post(form, url);
            }

            /**
             *
             * @param todoList
             * @returns {*}
             */
            function saveTodoPrintLogs(todoList) {
                let form = {
                    'todos': _.pluck(todoList, 'id')
                };
                let url = `/todo/activities`;
                return httpService.post(form, url);
            }
        });

})();