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
    angular.module('ManagerApp', ['ngRoute', 'ngCookies', 'ngDialog', 'ngAnimate', 'ngSanitize',
        'ui.bootstrap', 'ui.sortable', "com.2fdevs.videogular", "com.2fdevs.videogular.plugins.controls",
        "com.2fdevs.videogular.plugins.buffering", '720kb.datepicker', 'timeLine', 'chart.js', 'toaster', 'cgPrompt',
        'angularAudioRecorder', 'ngFileUpload', 'ngAudio', 'webcam', 'color.picker', 'cfp.hotkeys', 'view.file',
        'angularMoment', 'indexedDB', 'angular-spinkit', 'infinite-scroll', 'wu.masonry', 'fancyboxplus', 'ngPrint',
        'app.services', 'app.filters', 'app.components', 'app.directives', 'app.constant', 'colon_cancers', 'a1c',
        'medication', 'problems', 'todos', 'medication-component', 'inr', 'document', 'TemplateCache','app.searchModule'])
        .config(function ($routeProvider, recorderServiceProvider, ChartJsProvider, $httpProvider, $indexedDBProvider) {
            console.log("config");
            $indexedDBProvider.connection('andromedaHealthIndexedDB')
                .upgradeDatabase(1, function (event, db, tx) {
                    let objStore = db.createObjectStore('encounter', {keyPath: 'id'});
                    objStore.createIndex('audio_idx', 'audio', {unique: false});
                });
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

            /**
             * Configuration for recording service
             */
            recorderServiceProvider.forceSwf(false)
                .withMp3Conversion(true, {
                    bitRate: 32
                });
            /**
             * Global chart configuration
             */
            ChartJsProvider.setOptions({
                elements: {
                    line: {
                        tension: 0, // disables bezier curves
                    }
                },
                scales: {
                    xAxes: [
                        {
                            type: 'time',
                            time: {
                                minUnit: 'day'
                            }
                        }
                    ]
                },
                chartColors: ['#FFFFFF', '#FFFFFF', '#FFFFFF', '#FFFFFF', '#FFFFFF', '#FFFFFF', '#FFFFFF']
            });

            /**
             * Application route
             */
            $routeProvider
                .when('/', {
                    templateUrl: '/static/apps/patient/home-page/home.html',
                    controller: 'HomeCtrl'
                })
                .when('/edit/:section?', {
                    templateUrl: '/static/apps/patient/edit-profile-page/edit.html',
                    controller: 'EditUserCtrl'
                })
                .when('/problem/:problem_id', {
                    templateUrl: '/static/apps/patient/problem-page/problem.html',
                    controller: 'ProblemsCtrl'
                })
                .when('/goal/:goal_id', {
                    templateUrl: '/static/apps/patient/goal-page/goal.html',
                    controller: 'GoalsCtrl'
                })
                .when('/encounter/:encounter_id', {
                    templateUrl: '/static/apps/patient/encounter-page/encounter-page.template.html',
                    controller: 'EncounterPageCtrl'
                })
                .when("/todo/:todo_id", {
                    templateUrl: '/static/apps/patient/patient-todo-page/patient-todo-page.template.html',
                    controller: 'TodoCtrl'
                })
                .when('/manage/sharing', {
                    // templateUrl: '/static/apps/patient/manage-sharing/user-sharing.controller.js',
                    templateUrl: '/static/apps/patient/manage-sharing/manage_sharing_patient.html',
                    controller: 'ManageSharingPatientCtrl'
                })
                .when('/manage/sharing/problem/:sharing_patient_id', {
                    templateUrl: '/static/apps/patient/manage-sharing-problem/manage-sharing-problem.html',
                    controller: 'ManageSharingProblemCtrl'
                })
                .when('/medication/:medication_id', {
                    templateUrl: '/static/apps/patient/medication-page/medication-page.html',
                    controller: 'MedicationCtrl'
                })
                .when("/a1c/:a1c_id/add_different_order", {
                    templateUrl: '/static/apps/patient/a1c-new-order-page/add_different_order.html',
                    controller: 'AddDifferentOrderCtrl'
                })
                .when("/a1c/:a1c_id/enter_new_value", {
                    templateUrl: '/static/apps/patient/a1c-new-value-page/enter_new_value.html',
                    controller: 'EnterNewValueCtrl'
                })
                .when("/a1c/:a1c_id/edit_or_delete_values", {
                    templateUrl: '/static/apps/patient/a1c-edit-delete-value-page/edit_or_delete_values.html',
                    controller: 'EditOrDeleteValuesCtrl'
                })
                .when("/observation_value/:value_id/edit_value", {
                    templateUrl: '/static/apps/patient/a1c-edit-value-page/edit_value.html',
                    controller: 'EditValueCtrl'
                })
                .when('/data/view', {
                    templateUrl: '/static/apps/patient/observation-table-page/vitals_table_view_ctrl.html',
                    controller: 'ObservationTableCtrl'
                })
                .when('/data/:data_id', {
                    templateUrl: '/static/apps/patient/observation-page/data.html',
                    controller: 'DataCtrl'
                })
                .when('/data/:data_id/add_data', {
                    templateUrl: '/static/apps/patient/observation-add-data-page/add_data.html',
                    controller: 'AddDataCtrl'
                })
                .when('/data/:data_id/show_all_data', {
                    templateUrl: '/static/apps/patient/observation-list-data-page/show_all_data.html',
                    controller: 'ShowAllDataCtrl'
                })
                .when('/data/:dataId/edit/:componentValueIds', {
                    templateUrl: '/static/apps/patient/observation-data-detail-page/edit_data.html',
                    controller: 'IndividualDataCtrl'
                })
                .when('/data/:data_id/settings', {
                    templateUrl: '/static/apps/patient/observation-setting-page/settings.html',
                    controller: 'DataSettingsCtrl'
                })
                .when('/document/:documentId', {
                    templateUrl: '/static/apps/document-detail-page/document-page.template.html',
                    controller: 'ViewDocumentCtrl',
                })
                .when('/todo-laboratory/:todoId', {
                    templateUrl: '/static/apps/patient/todo-laboratory-print-page/print.template.html',
                    controller: 'PrintCtrl'
                })
                .otherwise('/');
        })
        .factory('CollapseService', function (hotkeys, $location, $timeout, $rootScope, patientService, ngDialog) {
            console.log("factory");
            let CollapseService = {
                show_homepage_tab: 'problems',
                show_colon_collapse: false,
                show_a1c_collapse: false,
                show_inr_collapse: false,
                innerProblemTabSetActive: 0,
                ChangeColonCollapse: ChangeColonCollapse,
                ChangeA1cCollapse: ChangeA1cCollapse,
                ChangeHomepageTab: ChangeHomepageTab,
                ChangeInrCollapse: ChangeInrCollapse,
                initHotKey: initHotKey
            };
            return CollapseService;

            function ChangeColonCollapse() {
                CollapseService.show_colon_collapse = !CollapseService.show_colon_collapse;
            }

            function ChangeA1cCollapse() {
                CollapseService.show_a1c_collapse = !CollapseService.show_a1c_collapse;
            }

            function ChangeHomepageTab(tab) {
                CollapseService.show_homepage_tab = tab;
            }

            function ChangeInrCollapse() {
                CollapseService.show_inr_collapse = !CollapseService.show_inr_collapse;
            }

            function initHotKey() {
                hotkeys.add({
                    combo: 'ctrl+shift+h',
                    description: 'Open Fit & Well',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        $location.path(`/problem/${$('#fit_and_well').val()}`);
                    }
                });

                hotkeys.add({
                    combo: 'ctrl+i',
                    description: 'Go to Problem tab',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        CollapseService.ChangeHomepageTab('problems');
                        CollapseService.innerProblemTabSetActive = 0;

                        $location.path('/');

                        setTimeout(() => {
                            window.scrollTo(0, $(".tab-problems").position().top);
                        }, 100);
                    }
                });

                hotkeys.add({
                    combo: 'ctrl+s',
                    description: 'Go to My story tab',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        CollapseService.ChangeHomepageTab('mystory');

                        $location.path('/');

                        $rootScope.$broadcast('tabPressed', {});
                    }
                });
                hotkeys.add({
                    combo: 'ctrl+d',
                    description: 'Go to Data tab',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        CollapseService.ChangeHomepageTab('data');
                        $location.path('/');
                    }
                });
                hotkeys.add({
                    combo: 'ctrl+m',
                    description: 'Go to Medication tab',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        CollapseService.ChangeHomepageTab('medication');
                        $location.path('/');
                    }
                });
                hotkeys.add({
                    combo: 'ctrl+shift+i',
                    description: 'Go to add new problem',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        CollapseService.ChangeHomepageTab('problems');
                        CollapseService.innerProblemTabSetActive = 2;
                        $location.path('/');
                    }
                });
                hotkeys.add({
                    combo: 'ctrl+shift+m',
                    description: 'Go to add new medication',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        CollapseService.ChangeHomepageTab('medication');
                        $location.path('/');
                        $timeout(function () {
                            $('medication input[type=text]').focus();
                        }, 500);
                    }
                });
                hotkeys.add({
                    combo: 'ctrl+c',
                    description: 'Copy most recent encounter to clipboard',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        // Showing loading indicator
                        ngDialog.open({
                            template: 'copyEncounterDialog',
                            showClose: false,
                            controller: function (patientService, toaster) {
                                let vm = this;
                                vm.dataIsLoaded = false;
                                vm.$temp = null;


                                // Load most recent encounter a.k.a latest
                                patientService.getMostRecentEncounter($('#patient_id').val()).then((data) => {
                                    let text = '';

                                    // Copy encounter summaries
                                    if (data.most_recent_encounter_summaries.length > 0) {
                                        text += "All the encounter summaries from the most recent encounter: \r\n";
                                        angular.forEach(data.most_recent_encounter_summaries, function (value, key) {
                                            let container = $("<div/>");
                                            container.append(value);
                                            text += `${container.text()}\r`;
                                        });
                                        text += '\r\n';
                                    }

                                    // Refer https://trello.com/c/cFylaLdv
                                    if (data.most_recent_encounter_documents.length > 0) {
                                        text += "Measured today: \r\n";
                                        angular.forEach(data.most_recent_encounter_documents, function (value, key) {
                                            let container = $("<div/>");
                                            container.append(`${value.name} : ${value.value}`);
                                            text += `${container.text()} \r\n`;
                                        });
                                        text += '\r\n';
                                    }

                                    // Copy related problem
                                    if (data.most_recent_encounter_related_problems.length > 0) {
                                        text += "List of related problems : \r\n";
                                        angular.forEach(data.most_recent_encounter_related_problems, function (value, key) {
                                            text += value.problem_name + '\r\n';
                                        });
                                        text += '\r\n';
                                    }

                                    // Copy pending all todo
                                    text += "List of all active todos : \r\n";
                                    angular.forEach(data.todo, function (value, key) {
                                        text += `${value.todo} ${value.problem ? 'for problem ' + value.problem.problem_name : ''}\r\n`;
                                    });

                                    // Copy to clipboard
                                    vm.$temp = $("<textarea/>");
                                    vm.$temp.val(text);
                                    $("body").append(vm.$temp);

                                    vm.dataIsLoaded = true;

                                    // TODO: Focus
                                    setTimeout(() => {
                                        $(".ngdialog-buttons button").focus()
                                    }, 200);

                                });

                                vm.copy = function () {
                                    vm.$temp.select();
                                    document.execCommand("copy");
                                    vm.$temp.remove();

                                    toaster.pop('success', 'Done', 'Data is copied to clipboard');

                                }
                            },
                            controllerAs: 'vm'
                        });
                    }
                });
                hotkeys.add({
                    combo: 'tab',
                    description: 'Navigate through My Story text component',
                    allowIn: ['INPUT', 'TEXTAREA', 'SELECT'],
                    callback: function (event, hotkey) {
                        $rootScope.$broadcast('tabPressed', null);
                    }
                });
            }
        })
        .run(function (CollapseService, sharedService, $rootScope) {
            console.log("run");
            $rootScope.$on('$routeChangeSuccess',(angularEvent,current,previous)=>{
               $rootScope.currentPage = current.$$route.controller;
            });

            sharedService.getSettings().then(function (response) {
                angular.forEach(response.data.settings, function (value, key) {
                    sharedService.settings[key] = JSON.parse(value);
                });
            });

            CollapseService.initHotKey();
        });
})();