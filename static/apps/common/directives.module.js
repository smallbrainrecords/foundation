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

    var bodyParts = [{
        'name': 'head part',
        'center': [100, 35],
        'radius': 30,
        'snomed_id': '123850002',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'neck structure',
        'coordinates': [
            [90, 70],
            [110, 70],
            [110, 90],
            [90, 90]
        ],
        'snomed_id': '45048000',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'structureThoracic spine ',
        'coordinates': [
            [90, 95],
            [110, 95],
            [110, 160],
            [90, 160]
        ],
        'snomed_id': '122495006',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Lumbar spine structure',
        'coordinates': [
            [90, 165],
            [110, 165],
            [110, 220],
            [90, 220]
        ],
        'snomed_id': '122496007',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'R thorax structure ',
        'coordinates': [
            [40, 95],
            [85, 95],
            [85, 135]
        ],
        'snomed_id': '51872008',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of right shoulder region',
        'center': [30, 110],
        'radius': 10,
        'snomed_id': '91774008',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Right upper arm structure',
        'coordinates': [
            [20, 125],
            [40, 125],
            [40, 178],
            [20, 178]
        ],
        'snomed_id': '368209003',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Right elbow region structure',
        'center': [30, 190],
        'radius': 8,
        'snomed_id': '368149001',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of right forearm',
        'coordinates': [
            [20, 200],
            [40, 200],
            [40, 240],
            [20, 240]
        ],
        'snomed_id': '64262003',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of right wrist ',
        'center': [30, 252],
        'radius': 8,
        'snomed_id': '9736006',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of right hand',
        'coordinates': [
            [20, 265],
            [40, 265],
            [40, 275],
            [20, 275]
        ],
        'snomed_id': '78791008',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Right hip region structure',
        'center': [65, 233],
        'radius': 12,
        'snomed_id': '287579007',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of right thigh',
        'coordinates': [
            [55, 250],
            [75, 250],
            [75, 315],
            [55, 315]
        ],
        'snomed_id': '11207009',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of right knee',
        'center': [65, 330],
        'radius': 10,
        'snomed_id': '6757004',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of right lower leg',
        'coordinates': [
            [55, 345],
            [75, 345],
            [75, 395],
            [55, 395]
        ],
        'snomed_id': '32696007',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of right ankle',
        'center': [65, 410],
        'radius': 10,
        'snomed_id': '6685009',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of right foot',
        'coordinates': [
            [55, 425],
            [75, 425],
            [75, 440],
            [55, 440]
        ],
        'snomed_id': '7769000',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'L thorax structure ',
        'coordinates': [
            [160, 95],
            [115, 95],
            [115, 135]
        ],
        'snomed_id': '40768004',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of left shoulder region',
        'center': [170, 110],
        'radius': 10,
        'snomed_id': '91775009',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Left upper arm structure',
        'coordinates': [
            [160, 125],
            [180, 125],
            [180, 178],
            [160, 178]
        ],
        'snomed_id': '368208006',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Left elbow region structure',
        'center': [170, 190],
        'radius': 8,
        'snomed_id': '368148009',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of left forearm',
        'coordinates': [
            [160, 200],
            [180, 200],
            [180, 240],
            [160, 240]
        ],
        'snomed_id': '66480008',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of left wrist ',
        'center': [170, 252],
        'radius': 8,
        'snomed_id': '5951000',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of left hand',
        'coordinates': [
            [160, 265],
            [180, 265],
            [180, 275],
            [160, 275]
        ],
        'snomed_id': '85151006',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Left hip region structure',
        'center': [135, 233],
        'radius': 12,
        'snomed_id': '287679003',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of left thigh',
        'coordinates': [
            [125, 250],
            [145, 250],
            [145, 315],
            [125, 315]
        ],
        'snomed_id': '61396006',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of left knee',
        'center': [135, 330],
        'radius': 10,
        'snomed_id': '82169009',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of left lower leg',
        'coordinates': [
            [125, 345],
            [145, 345],
            [145, 395],
            [125, 395]
        ],
        'snomed_id': '48979004',
        'status': 'gray',
        'shape_type': 'polygon'
    }, {
        'name': 'Structure of left ankle',
        'center': [135, 410],
        'radius': 10,
        'snomed_id': '51636004',
        'status': 'gray',
        'shape_type': 'circle'
    }, {
        'name': 'Structure of left foot',
        'coordinates': [
            [125, 425],
            [145, 425],
            [145, 440],
            [125, 440]
        ],
        'snomed_id': '22335008',
        'status': 'gray',
        'shape_type': 'polygon'
    }];

    function process_pain_data(painAvatars) {


        for (var i = painAvatars.length - 1; i > -1; i--) {
            if (i + 1 < painAvatars.length) {
                for (var key in painAvatars[i]['json']) {
                    if (painAvatars[i]['json'][key] == 'gray' && (painAvatars[i + 1]['json'][key] == 'red' || painAvatars[i + 1]['json'][key] == 'green')) {
                        painAvatars[i]['json'][key] = 'green';
                    }
                }
            }
        }


        return painAvatars;
    }

    function startSlideshow(painAvatars) {
        window.t = 0;
        $('.pain_avatar').hide();
        $('#pain_avatar' + t).show();
        $('#pain_avatar' + t + ' p').append(' (' + (t + 1) + '/' + painAvatars.length + ')');
        window.slideshow = setInterval(function () {
            if (t + 1 < painAvatars.length) {
                $('.pain_avatar').hide();
                t += 1;
                $('#pain_avatar' + t).show();
            } else {
                $('#pain_avatar' + t).append(' End of slideshow');
                $('#toggleSlideshow').val('Start slideshow');
                clearInterval(window.slideshow)
            }
        }, 2000);
    }

    function stopSlideshow() {
        clearInterval(window.slideshow);
        var t = 0;
        $('.pain_avatar').hide();
        $('#pain_avatar' + t).show();
    }

    function forwards(painAvatars) {
        if (t + 1 == painAvatars.length) {
            t = -1;
        }
        $('.pain_avatar').hide();
        window.t += 1;
        $('#pain_avatar' + window.t).show();
    }

    function backwards(painAvatars) {
        if (t - 1 == -1) {
            t = painAvatars.length;
        }
        $('.pain_avatar').hide();
        window.t -= 1;
        $('#pain_avatar' + window.t).show();
    }

    function setGlobalPlayer(id) {

        if (typeof (videojs) == 'undefined') {

            setTimeout(function () {
                setGlobalPlayer(id);
            }, 2000);
        } else {
            window.player = videojs(id);
        }
    }

    angular.module('app.directives', [])
        .config(function ($httpProvider) {
            $httpProvider.defaults.xsrfCookieName = 'csrftoken';
            $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        }).directive('painAvatar', ['$parse',
        function ($parse) {


            return {

                scope: {
                    // creates a scope variable in your directive
                    // called `locations` bound to whatever was passed
                    // in via the `locations` attribute in the DOM
                    pain_data: '=painData'
                },
                link: function ($scope, $element, $attrs) {

                    $element.html("Pain Avatar");

                    $scope.$watch('pain_data', function (pain_data) {

                        //console.log(pain_data);
                        if (pain_data == undefined) {
                            return false;
                        }

                        /******* Render Pain Avatar ***************/


                        pain_data = process_pain_data(pain_data);

                        var control_ui = '<div id="controls" style="background:whitesmoke">';
                        control_ui += '<input type="button" id="toggleSlideshow" value="Start slideshow">';

                        control_ui += '<input type="button" id="backwards" value="<">';
                        control_ui += '<input type="button" id="forwards" value=">">';

                        control_ui += '</div>';


                        $element.append(control_ui);

                        for (var i = 0; i < pain_data.length; i++) {


                            var canvas_html = '<div class="pain_avatar" id="pain_avatar' + i + '"> ';
                            canvas_html += '<canvas id="myCanvas' + i + '" width="214" height="442" style="background:#FFF; border:1px solid #000000;"></canvas>';
                            canvas_html += '<p>' + pain_data[i]['datetime'] + ' (' + (i + 1) + '/' + pain_data.length + ')</p>';
                            canvas_html += '</div>';

                            $element.append(canvas_html);

                            for (var j = 0; j < bodyParts.length; j++) {

                                var c = bodyParts[j];
                                var ctx = document.getElementById("myCanvas" + i).getContext("2d");
                                ctx.fillStyle = pain_data[i]['json'][bodyParts[j]['snomed_id']];
                                ctx.beginPath();
                                if (c['shape_type'] == 'polygon') {

                                    ctx.moveTo(c['coordinates'][0][0], c['coordinates'][0][1]);
                                    for (var k = 1; k < c['coordinates'].length; k++) {
                                        ctx.lineTo(c['coordinates'][k][0], c['coordinates'][k][1]);
                                    }
                                } else {
                                    ctx.arc(c['center'][0], c['center'][1], c['radius'], 0, 2 * Math.PI, false);
                                }
                                ctx.closePath();
                                ctx.fill();
                            }
                        }

                        window.t = 0;

                        $('.pain_avatar').hide();
                        $('#pain_avatar' + t).show();


                        $('#toggleSlideshow').click(function (e) {
                            //alert($(this).val());
                            if ($(this).val() == 'Start slideshow') {
                                startSlideshow(pain_data);
                                $(this).val('Stop slideshow');
                            } else {
                                stopSlideshow();
                                $(this).val('Start slideshow');
                            }
                        });
                        $('#forwards').click(function (e) {
                            forwards(pain_data);
                        });
                        $('#backwards').click(function (e) {
                            backwards(pain_data);
                        });


                        /******* End of Render Pain Avatar ***************/
                    });

                }
            }


        }
    ])
        .directive('fileModel', ['$parse', function ($parse) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var model = $parse(attrs.fileModel);
                    var modelSetter = model.assign;


                    element.bind('change', function () {
                        scope.$apply(function () {
                            modelSetter(scope, element[0].files[0]);
                        });
                    });
                }
            };
        }])
        .directive('ngVideoPlayerJump', ['$parse', function ($parse) {
            return {
                restrict: 'A',
                link: function ($scope, $element, $attrs) {

                    var video_seconds = $attrs.videoSeconds;

                    $element.click(function () {
                        window.player.play();
                        window.player.currentTime(video_seconds);
                    });
                }
            };
        }])
        .directive('ngVideoPlayer', function ($compile) {

            var component = {};

            component.restrict = 'A';
            component.link = function ($scope, $element, $attrs) {

                var id = $attrs.videoId;
                $scope.video_id = id;
                $scope.video_src = $attrs.videoSrc;
                $scope.video_type = $attrs.videoType;


                var template = '';

                template += '<video id="{{video_id}}" class="video-js vjs-default-skin" ';
                template += ' controls preload="auto" width="640" height="264" ';
                template += ' > ';
                template += '<source src="{{video_src}}" type="{{video_type}}" />';
                template += '</video>';

                $scope.$watch($attrs.videoSrc, function (newVal, oldVal) {

                    $scope.video_src = newVal;

                    if (oldVal == undefined) {
                        var elem_html = $compile(template)($scope);
                        $element.html(elem_html);
                        setGlobalPlayer(id);
                    }
                });


            };


            return component;

        })
        .directive('ngAudioPlayerJump', ['$parse', function ($parse) {
            return {
                restrict: 'A',
                link: function ($scope, $element, $attrs) {

                    var audio_seconds = $attrs.audioSeconds;

                    $element.click(function () {
                        var myAudio = document.getElementById('audio1');
                        myAudio.currentTime = audio_seconds;
                        myAudio.play();
                    });
                }
            };
        }])
        .directive('ngAudioPlayer', ['$parse', function ($parse) {

            var component = {};

            component.restrict = 'A';
            component.link = function ($scope, $element, $attr) {

                $scope.audio_src = $attr.audioSrc;
                $scope.audio_type = $attr.audioType;
            };


            component.template = function ($element, $attr) {
                var template = '';
                template += '<audio controls id="audio1" preload="auto">';
                template += '<source src="{{audio_src}}" type="{{audio_type}}" >';
                template += 'Your browser does not support the audio element.';
                template += '</audio>';

                return template;

            };

            return component;
        }])
        .directive('fixedZone', ['$parse', function ($parse) {

            return {

                link: function ($scope, $element, $attrs) {


                    if ($(window).width() < 1200) {
                        return false;
                    }

                    var offset_orientation = $attrs.offsetOrientation;

                    if (offset_orientation == 'top') {

                        var offset_top = parseInt($attrs.offsetTop);
                        $element.affix({
                            offset: {top: offset_top}
                        });

                    } else {

                        var offset_bottom = parseInt($attrs.offsetBottom);
                        $element.affix({
                            offset: {
                                top: offset_bottom
                            }
                        });


                    }

                }


            }
        }])
        .directive('patientHomepageTimeRangeSelector', ['$parse', function ($parse) {

            return {
                link: function ($scope, $element, $attrs) {
                    setTimeout(function () {

                        var offset_top = $("#clinical-staff-note").outerHeight(true) + $("#clinical-staff-todo").outerHeight(true) + $("#patient-profile-header").outerHeight(true);
                        $element.affix({
                            offset: {top: offset_top}
                        });
                    }, 3000);
                }
            }
        }])
        .directive('onFileChange', function () {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var onChangeHandler = scope.$eval(attrs.onFileChange);

                    element.bind('change', function () {
                        scope.$apply(function () {
                            var files = element[0].files;
                            if (files) {
                                onChangeHandler(files);
                            }
                        });
                    });

                }
            };
        })
        .directive('autoFocus', function ($timeout) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    $timeout(function () {
                        element.focus();
                    }, 500);
                }
            };
        });
})();
