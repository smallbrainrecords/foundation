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
    angular.module('app.constant', [])
        .constant('RECORDER_STATUS', {
            isRecording: 0,
            isPaused: 1,
            isStopped: 2
        })
        .constant('AUDIO_UPLOAD_STATUS', {
            isInitialize: 0,
            isUploading: 1,
            isUploaded: 2
        })
        .constant('LABELS', [
            {name: 'green', css_class: 'todo-label-green'},
            {name: 'yellow', css_class: 'todo-label-yellow'},
            {name: 'orange', css_class: 'todo-label-orange'},
            {name: 'red', css_class: 'todo-label-red'},
            {name: 'purple', css_class: 'todo-label-purple'},
            {name: 'blue', css_class: 'todo-label-blue'},
            {name: 'sky', css_class: 'todo-label-sky'},
        ])
        .constant('VIEW_MODES', [
            {label: 'All', value: 0},
            {label: 'Week', value: 1},
            {label: 'Month', value: 2},
            {label: 'Year', value: 3},
        ])
        .constant('TODO_LIST', {
            'NONE': 0,
            'INR': 1,
            'A1C': 2,
            'COLON_CANCER_SCREENING': 3
        })
        .constant('PROBLEM_NOTE_TYPE', {
            WIKI: 'wiki',
            HISTORY: 'history'
        });
})();