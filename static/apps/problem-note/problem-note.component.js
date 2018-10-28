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
        .component('problemNote', {
            templateUrl: '/static/apps/problem-note/problem-note.template.html',
            controller: ProblemNoteController,
            bindings: {
                problemId: "<",
                onNoteAdded: "&"
            }
        });


    function ProblemNoteController(PROBLEM_NOTE_TYPE, problemService, toaster) {
        let ctrl = this;

        // Properties
        ctrl.note = "";
        ctrl.latestNote = null;

        // Current show item to be shown
        ctrl.noteList = [];

        // Always be 10 items or empty on zero
        ctrl.noteStorage = [];
        // Methods
        ctrl.addNote = addNote;
        ctrl.loadMoreNotes = loadMoreNotes;

        ctrl.$onInit = () => {
            // On init load 11 items then show only 1st and next 10 items
            fetchProblemNotes(11, initCallBack);

            // On click '4 more notes' show next 10 items in list and load addition next 10 items
        };

        /**
         * Adding new wiki note. After a wiki note is added a corresponding to do is auto generated.
         * Post action: https://trello.com/c/ZFlgZLOz
         * TODO: Generate todo item
         */
        function addNote() {
            let form = {
                note: ctrl.note,
                note_type: PROBLEM_NOTE_TYPE.WIKI
            };

            problemService.addNote(ctrl.problemId, form)
                .then(response => {
                    if (response.data.success) {
                        // Notify
                        toaster.pop('success', 'Done', 'Wiki note added');

                        // Pushed to latest note
                        ctrl.noteList.unshift(ctrl.latestNote);

                        // Newly note added is latest one
                        ctrl.latestNote = response.data.note;

                        // Reset the form
                        ctrl.note = "";

                        // https://trello.com/c/ZFlgZLOz. Move cursor to todo input text field
                        $('#todoNameInput').focus();

                        // Push newly added todo to active todo list
                        if (response.data.hasOwnProperty('todo')) {
                            patientService.addTodoCallback(response.data.todo);
                        }
                    } else {
                        toaster.pop('error', 'Warning', 'Action Failed');
                    }
                }, () => {
                    toaster.pop('error', 'Warning', 'Something went wrong!');
                });
        }

        /**
         * Loading more 10 problem's note regardless of problem note's author
         * @param {Number} limit
         */
        function loadMoreNotes(limit = 10) {
            // First showing more item
            if (ctrl.noteStorage.length === 0) {
                toaster.pop('warning', 'Warning', "No more notes");
                return;
            } else {
                ctrl.noteList = ctrl.noteList.concat(ctrl.noteStorage);
            }

            // Second feed local item
            fetchProblemNotes(limit);
        }

        /**
         *
         * @param limit
         * @param callback
         */
        function fetchProblemNotes(limit, callback) {
            let lastLoadedItem = ctrl.noteStorage[ctrl.noteStorage.length - 1];

            problemService.loadMoreProblemNotes(ctrl.problemId, PROBLEM_NOTE_TYPE.WIKI, lastLoadedItem == null ? null : lastLoadedItem.id, limit)
                .then(response => {
                    if (response.data.success) {
                        ctrl.noteStorage = response.data.notes;
                        if (callback) callback();
                    }
                }, () => {
                    toaster.pop('error', 'Warning', 'Something went wrong!');
                });
        }

        /**
         *
         */
        function initCallBack() {
            ctrl.latestNote = ctrl.noteStorage.shift();
        }
    }
})();