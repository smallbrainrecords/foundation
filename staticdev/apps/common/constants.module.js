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
        });
})();