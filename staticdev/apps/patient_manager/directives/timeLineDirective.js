var timeLine = angular.module('timeLine', []);

timeLine.directive('problemTimeline', timelineDirective);

function timelineDirective() {

    var timeline = {}; 

            timeline.renderPath = function (c, d, path) {
                !path && (path = timeline.wrapSvg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'path')));
                path.setAttribute('d', c.d || d);
                path.setAttribute('class', c.class || c);
                path.setAttribute('display', 'inline');
                return path;
            }
            timeline.renderText = function (c, x, y, txt, text) {
                !text && (text = timeline.wrapSvg.appendChild(document.createElementNS('http://www.w3.org/2000/svg', 'text')));
                for (var iii = 0; iii < text.childNodes.length; text.childNodes[iii] && text.removeChild(text.childNodes[iii]), iii++);
                text.setAttribute('x', c.x || x);
                text.setAttribute('y', c.y || y);
                text.setAttribute('class', c.c || c);
                text.setAttribute('pointer-events', 'none');
                text.setAttribute('display', 'inline');
                text.appendChild(document.createTextNode(txt));
                return text;
            }
            timeline.Undo = function (s) { if (!timeline.isEdit) { return; }; timeline.unrd&&(timeline.unrd--, timeline.init()); }
            timeline.Redo = function (s) { if (!timeline.isEdit) { return; };(timeline.dat.length > ++timeline.unrd) && timeline.init() || timeline.unrd-- }
            timeline.Save = function (s) {
                if (!timeline.isEdit) { return; };
                var sarr = JSON.parse(JSON.stringify(timeline.dat[timeline.unrd]));
                for (var iii = 0, eee = 0; iii < sarr.problems.length; delete sarr.problems[iii].events[eee].hidden, eee++, (eee < sarr.problems[iii].events.length) || (!sarr.problems[iii].events[eee - 1].state && sarr.problems[iii].events.pop(), eee = 0, iii++));
                s.timelineSave(sarr);
            }

            timeline.viewAll = function () {
                for (var iii = 0; iii < timeline.zoomArr.length; timeline.zoomArr[iii].setAttribute('class', 'G1'), iii++);
                timeline.zoomArr[0].setAttribute('class', 'S1');
                timeline.hideAll(timeline.g01Arr); timeline.hideAll(timeline.g02Arr); timeline.hideAll(timeline.txtArr);
                timeline.dat[timeline.unrd].birthday = timeline.dat[timeline.unrd].birthday || '15/11/1970 12:00:00';
                var bdy = timeline.dat[timeline.unrd].birthday.split('/'); bdy = new Date(bdy[1] + '/' + bdy[0] + '/' + bdy[2]).getFullYear();
                var ViewDays = (+timeline.now.getFullYear() - bdy) * 365, fvX = timeline.renderXw / ViewDays;
                console.log('bdy ' +bdy);
                timeline.szoom = {};
                timeline.szoom.viewMS = ViewDays * 24 * 60 * 60 * 1000;
                timeline.szoom.start = timeline.now.getTime() - timeline.szoom.viewMS;
                timeline.arrowl.onclick = function () { return; }
                timeline.arrowr.onclick = function () { return; }
                for (var iii = (timeline.now.getMonth() + 1) * 30, s = 0, m = timeline.now.getFullYear(), xxx = 0 ; iii < ViewDays; xxx++, iii = iii + (365*5)) {
                    s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                    timeline.g01Arr[xxx] = timeline.renderPath('G0', 'M' + s + ',' + (timeline.renderYst) + ' l0,500 l1 0 l0 -500 z', timeline.g01Arr[xxx]);
                    timeline.g02Arr[xxx] = timeline.renderPath('G1', 'M' + (s - 1) + ',' + timeline.renderYst + ' l0,40 l3 0 l0 -40 z', timeline.g02Arr[xxx]);
                    timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, m, timeline.txtArr[xxx]);
                    m -= 5;
                }
                s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, m, timeline.txtArr[xxx]);
                timeline.init();
            }
            timeline.view10y = function () {
                for (var iii = 0; iii < timeline.zoomArr.length; timeline.zoomArr[iii].setAttribute('class', 'G1'), iii++);
                timeline.zoomArr[1].setAttribute('class', 'S1');
                timeline.hideAll(timeline.g01Arr); timeline.hideAll(timeline.g02Arr); timeline.hideAll(timeline.txtArr);
                timeline.szoom = {};
                timeline.szoom.viewMS = 3654 * 24 * 60 * 60 * 1000;
                timeline.szoom.start = timeline.now.getTime() - timeline.szoom.viewMS;
                timeline.arrowl.onclick = function () { timeline.now = new Date(timeline.now.getTime() - timeline.szoom.viewMS); timeline.view10y(); }
                timeline.arrowr.onclick = function () { (new Date().getTime() > timeline.now.getTime()) && (timeline.now = new Date(timeline.now.getTime() + timeline.szoom.viewMS), (new Date().getTime() >= timeline.now.getTime())) || (timeline.now = new Date()); timeline.view10y(); }
                var ViewDays = 3654, fvX = timeline.renderXw / ViewDays;
                for (var iii = (timeline.now.getMonth()+1)*30, s = 0, m = timeline.now.getFullYear(), xxx = 0 ; iii < ViewDays; xxx++, iii = iii + 365) {
                    s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                    timeline.g01Arr[xxx] = timeline.renderPath('G0', 'M' + s + ',' + (timeline.renderYst) + ' l0,500 l1 0 l0 -500 z', timeline.g01Arr[xxx]);
                    timeline.g02Arr[xxx] = timeline.renderPath('G1', 'M' + (s - 1) + ',' + timeline.renderYst + ' l0,40 l3 0 l0 -40 z', timeline.g02Arr[xxx]);
                    timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, m--, timeline.txtArr[xxx]);
                }
                s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, m, timeline.txtArr[xxx]);
                timeline.init();
            }

            timeline.view1y = function () {
                for (var iii = 0; iii < timeline.zoomArr.length; timeline.zoomArr[iii].setAttribute('class', 'G1'), iii++);
                timeline.zoomArr[2].setAttribute('class', 'S1');
                timeline.hideAll(timeline.g01Arr); timeline.hideAll(timeline.g02Arr); timeline.hideAll(timeline.txtArr);
                timeline.szoom = { };
                timeline.szoom.viewMS = 365 * 24 * 60 * 60 * 1000;
                timeline.szoom.start = timeline.now.getTime() - timeline.szoom.viewMS;
                timeline.arrowl.onclick = function () { timeline.now = new Date(timeline.now.getTime() - timeline.szoom.viewMS); timeline.view1y(); }
                timeline.arrowr.onclick = function () { (new Date().getTime() > timeline.now.getTime()) && (timeline.now = new Date(timeline.now.getTime() + timeline.szoom.viewMS), (new Date().getTime() >= timeline.now.getTime())) || (timeline.now = new Date()); timeline.view1y(); }
                var ViewDays=365,fvX=timeline.renderXw/ViewDays;
                for (var iii = timeline.now.getDate(), s = 0, m = timeline.now.getMonth(), xxx=0 ; iii < ViewDays; !~m && (m = 11), xxx++, iii = iii + 30) {
                    s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                    timeline.g01Arr[xxx] = timeline.renderPath('G0', 'M' + s + ',' + (timeline.renderYst) + ' l0,500 l1 0 l0 -500 z', timeline.g01Arr[xxx]);
                    timeline.g02Arr[xxx] = timeline.renderPath('G1', 'M' + (s - 1) + ',' + timeline.renderYst + ' l0,40 l3 0 l0 -40 z', timeline.g02Arr[xxx]);
                    timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, timeline.months[m--], timeline.txtArr[xxx]);
                }
                s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, timeline.months[m], timeline.txtArr[xxx]);
                timeline.init();
            }
                

            timeline.view6m = function () {
                for (var iii = 0; iii < timeline.zoomArr.length; timeline.zoomArr[iii].setAttribute('class', 'G1'), iii++);
                timeline.zoomArr[3].setAttribute('class', 'S1');
                timeline.szoom = {};
                timeline.szoom.viewMS = 183 * 24 * 60 * 60 * 1000;
                timeline.szoom.start = timeline.now.getTime() - timeline.szoom.viewMS;
                timeline.arrowl.onclick = function () { timeline.now = new Date(timeline.now.getTime() - timeline.szoom.viewMS); timeline.view6m(); }
                timeline.arrowr.onclick = function () { (new Date().getTime() > timeline.now.getTime()) && (timeline.now = new Date(timeline.now.getTime() + timeline.szoom.viewMS), (new Date().getTime() >= timeline.now.getTime())) || (timeline.now = new Date()); timeline.view6m(); }

                timeline.hideAll(timeline.g01Arr); timeline.hideAll(timeline.g02Arr); timeline.hideAll(timeline.txtArr);
                var ViewDays = 183, fvX = timeline.renderXw / ViewDays;
                for (var iii = timeline.now.getDate(), s = 0, m = timeline.now.getMonth(), xxx = 0 ; iii < ViewDays; !~m && (m = 11), xxx++, iii = iii + 30) {
                    s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                    timeline.g01Arr[xxx] = timeline.renderPath('G0', 'M' + s + ',' + (timeline.renderYst) + ' l0,500 l1 0 l0 -500 z', timeline.g01Arr[xxx]);
                    timeline.g02Arr[xxx] = timeline.renderPath('G1', 'M' + (s - 1) + ',' + timeline.renderYst + ' l0,40 l3 0 l0 -40 z', timeline.g02Arr[xxx]);
                    timeline.txtArr[xxx] = timeline.renderText('T1', (s + 20), timeline.renderYst + 20, timeline.months[m--], timeline.txtArr[xxx]);
                }
                s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, timeline.months[m], timeline.txtArr[xxx]);
                timeline.init();
            }

            timeline.view1m = function () {
                for (var iii = 0; iii < timeline.zoomArr.length; timeline.zoomArr[iii].setAttribute('class', 'G1'), iii++);
                timeline.zoomArr[4].setAttribute('class', 'S1');
                timeline.szoom = {};
                timeline.szoom.viewMS = 30 * 24 * 60 * 60 * 1000;
                timeline.szoom.start = timeline.now.getTime() - timeline.szoom.viewMS;
                timeline.arrowl.onclick = function () { timeline.now = new Date(timeline.now.getTime() - timeline.szoom.viewMS); timeline.view1m(); }
                timeline.arrowr.onclick = function () { (new Date().getTime() > timeline.now.getTime()) && (timeline.now = new Date(timeline.now.getTime() + timeline.szoom.viewMS), (new Date().getTime() >= timeline.now.getTime())) || (timeline.now = new Date()); timeline.view1m(); }
                timeline.hideAll(timeline.g01Arr); timeline.hideAll(timeline.g02Arr); timeline.hideAll(timeline.txtArr);
                var ViewDays = 30, fvX = timeline.renderXw / ViewDays;
                for (var iii = timeline.now.getDate()-(parseInt(timeline.now.getDate()/7)*7), s = 0, m = timeline.now.getMonth(), xxx = 0 ; iii < ViewDays; (timeline.now.getDate() == iii) && m--, !~m && (m = 11), xxx++, iii = iii + 7) {
                    s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                    timeline.g01Arr[xxx] = timeline.renderPath('G0', 'M' + s + ',' + (timeline.renderYst) + ' l0,500 l1 0 l0 -500 z', timeline.g01Arr[xxx]);
                    timeline.g02Arr[xxx] = timeline.renderPath('G1', 'M' + (s - 1) + ',' + timeline.renderYst + ' l0,40 l3 0 l0 -40 z', timeline.g02Arr[xxx]);
                    timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, (((timeline.now.getDate() - iii + 1) > 0) && (timeline.now.getDate() - iii + 1) || (timeline.now.getDate() - iii + 30)) + '-' + timeline.months[m], timeline.txtArr[xxx]);
                }
                s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                timeline.txtArr[xxx] = timeline.renderText('T1', (s + 25), timeline.renderYst + 20, (((timeline.now.getDate() - iii + 1) > 0) && (timeline.now.getDate() - iii + 1) || (timeline.now.getDate() - iii + 30)) + '-' + timeline.months[m], timeline.txtArr[xxx]);
                timeline.init();
            }
            timeline.view1w = function () {
                for (var iii = 0; iii < timeline.zoomArr.length; timeline.zoomArr[iii].setAttribute('class', 'G1'), iii++);
                timeline.zoomArr[5].setAttribute('class', 'S1');
                timeline.szoom = {};
                timeline.szoom.viewMS = 7 * 24 * 60 * 60 * 1000;
                timeline.szoom.start = timeline.now.getTime() - timeline.szoom.viewMS;
                timeline.arrowl.onclick = function () { timeline.now = new Date(timeline.now.getTime() - timeline.szoom.viewMS); timeline.view1w(); }
                timeline.arrowr.onclick = function () { (new Date().getTime() > timeline.now.getTime()) && (timeline.now = new Date(timeline.now.getTime() + timeline.szoom.viewMS), (new Date().getTime() >= timeline.now.getTime())) || (timeline.now = new Date()); timeline.view1w(); }
                timeline.hideAll(timeline.g01Arr); timeline.hideAll(timeline.g02Arr); timeline.hideAll(timeline.txtArr);
                var ViewDays = 7, fvX = timeline.renderXw / ViewDays;
                for (var iii = 1, s = 0, m = timeline.now.getMonth(), xxx = 0 ; iii < ViewDays; (timeline.now.getDate() == iii) && m--, !~m && (m = 11), xxx++, iii++) {
                    s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                    timeline.g01Arr[xxx] = timeline.renderPath('G0', 'M' + s + ',' + (timeline.renderYst) + ' l0,500 l1 0 l0 -500 z', timeline.g01Arr[xxx]);
                    timeline.g02Arr[xxx] = timeline.renderPath('G1', 'M' + (s - 1) + ',' + timeline.renderYst + ' l0,40 l3 0 l0 -40 z', timeline.g02Arr[xxx]);
                    timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, (timeline.now.getDate() -iii+1)+' ' + timeline.months[m], timeline.txtArr[xxx]);
                }
                s = (timeline.renderXst + ((ViewDays - iii) * fvX));
                timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, (timeline.now.getDate() - iii+1) + ' ' + timeline.months[m], timeline.txtArr[xxx]);
                timeline.init();
            }
            timeline.view1d = function () {
                for (var iii = 0; iii < timeline.zoomArr.length; timeline.zoomArr[iii].setAttribute('class', 'G1'), iii++);
                timeline.zoomArr[6].setAttribute('class', 'S1');
                timeline.szoom = {};
                timeline.szoom.viewMS = 1 * 24 * 60 * 60 * 1000;
                timeline.szoom.start = timeline.now.getTime() - timeline.szoom.viewMS;
                timeline.arrowl.onclick = function () { timeline.now = new Date(timeline.now.getTime() - timeline.szoom.viewMS); timeline.view1d(); }
                timeline.arrowr.onclick = function () { (new Date().getTime() > timeline.now.getTime()) && (timeline.now = new Date(timeline.now.getTime() + timeline.szoom.viewMS), (new Date().getTime() >= timeline.now.getTime())) || (timeline.now = new Date()); timeline.view1d(); }
                timeline.hideAll(timeline.g01Arr); timeline.hideAll(timeline.g02Arr); timeline.hideAll(timeline.txtArr);
                var ViewDays = 1, fvX = timeline.renderXw / ViewDays;
                for (var iii = 4, s = 0, m = timeline.now.getDate(), xxx = 0 ; iii < 24; (timeline.now.getHours() == iii) && m--, !~m && (m = 11), xxx++, iii=iii+4) {
                    s = (timeline.renderXst + ((ViewDays - (iii/24)) * fvX));
                    timeline.g01Arr[xxx] = timeline.renderPath('G0', 'M' + s + ',' + (timeline.renderYst) + ' l0,500 l1 0 l0 -500 z', timeline.g01Arr[xxx]);
                    timeline.g02Arr[xxx] = timeline.renderPath('G1', 'M' + (s - 1) + ',' + timeline.renderYst + ' l0,40 l3 0 l0 -40 z', timeline.g02Arr[xxx]);
                    timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, (24-iii) + ':00', timeline.txtArr[xxx]);
                }
                s = (timeline.renderXst + ((ViewDays - (iii/24)) * fvX));
                timeline.txtArr[xxx] = timeline.renderText('T1', (s + 15), timeline.renderYst + 20, timeline.now.getDate() + '-' + timeline.months[timeline.now.getMonth()], timeline.txtArr[xxx]);
                timeline.init();
            }

            timeline.init = function () {

                for(var iii=0;iii<timeline.dat[timeline.unrd].problems.length;iii++){
                    timeline.parr[iii] = timeline.parr[iii] || [];
                    if(!timeline.dat[timeline.unrd].problems[iii].events.length){continue;}
                    timeline.dat[timeline.unrd].problems[iii].events[timeline.dat[timeline.unrd].problems[iii].events.length - 1].state && timeline.dat[timeline.unrd].problems[iii].events.push({ startTime: new Date(new Date().setFullYear((new Date().getFullYear()) + 1)).strx() });
                    timeline.hideAll(timeline.parr[iii]);
                    timeline.larr[iii] = [];
                    for (var xxx = 0; xxx < timeline.dat[timeline.unrd].problems[iii].events.length; timeline.dat[timeline.unrd].problems[iii].events[xxx].hidden = timeline.drqq(timeline.dat[timeline.unrd].problems[iii].events[xxx].startTime), xxx++);
                    
                    for (xxx = 0; xxx < timeline.dat[timeline.unrd].problems[iii].events.length; timeline.drq(timeline.dat[timeline.unrd].problems[iii].events[xxx], iii, xxx), xxx++);
                    for (xxx = timeline.dat[timeline.unrd].problems[iii].events.length - 1; xxx >= 0; timeline.dat[timeline.unrd].problems[iii].events[xxx].hidden === 'G4' && (timeline.larr[iii].splice(0, 0, timeline.a(timeline.yarr[iii]), { 'class': 'G3 ' + (timeline.dat[timeline.unrd].problems[iii].events[xxx].state || 'inactive') }), xxx = 0), xxx--);
                    for (xxx = 0; xxx < timeline.dat[timeline.unrd].problems[iii].events.length; timeline.dat[timeline.unrd].problems[iii].events[xxx].hidden === 'G5' && (timeline.larr[iii].push(timeline.e(timeline.yarr[iii])), xxx = timeline.dat[timeline.unrd].problems[iii].events.length), xxx++);

                    timeline.drno4(iii);
                    timeline.drno5(iii);
                    timeline.drae(iii);
                    timeline.drm(iii);
                    timeline.dr(iii);
                }
                return true;
            }

            timeline.drno4 = function (ix) {
                for (xxx = 0; xxx < timeline.dat[timeline.unrd].problems[ix].events.length; xxx++) {
                    if (timeline.dat[timeline.unrd].problems[ix].events[xxx].hidden === 'G4') { continue; }
                    return;
                }
                timeline.larr[ix] = [];
            }
            timeline.drno5 = function (ix) {
                for (xxx = 0; xxx < timeline.dat[timeline.unrd].problems[ix].events.length; xxx++) {
                    if (timeline.dat[timeline.unrd].problems[ix].events[xxx].hidden === 'G5') { continue; }
                    return;
                }
                timeline.larr[ix] = [];
            }
            timeline.drae = function (ix) {
                if (!timeline.larr[ix].length) { return; }
                if (~timeline.larr[ix][0].class.indexOf('G2')) {
                    var ev = timeline.larr[ix][0].ev;
                    var d = ev.startTime, dd = d.split('/'); d = dd[1] + '/' + dd[0] + '/' + dd[2];
                    var x = ((new Date(d).getTime() - timeline.szoom.start) / (timeline.szoom.viewMS / timeline.renderXw)) + timeline.renderXst;
                    timeline.larr[ix][0] = timeline.q(x, timeline.yarr[ix], ev);
                }
                ~timeline.larr[ix][timeline.larr[ix].length - 1].class.indexOf('G3') && timeline.larr[ix].pop();
                if (~timeline.larr[ix][timeline.larr[ix].length - 1].class.indexOf('G2')) {
                    ev = timeline.larr[ix][timeline.larr[ix].length - 1].ev;
                    d = ev.startTime, dd = d.split('/'); d = dd[1] + '/' + dd[0] + '/' + dd[2];
                    x = ((new Date(d).getTime() - timeline.szoom.start) / (timeline.szoom.viewMS / timeline.renderXw)) + timeline.renderXst;
                    timeline.larr[ix][timeline.larr[ix].length - 1] = timeline.q(x, timeline.yarr[ix], ev);
                }
            }

            timeline.drq = function (ev, ix, xx) {
                if (ev.hidden|| ev.class) { return; }
                var d=ev.startTime, dd = d.split('/'); d = dd[1] + '/' + dd[0] + '/' + dd[2];
                var x = ((new Date(d).getTime() - timeline.szoom.start) / (timeline.szoom.viewMS / timeline.renderXw)) + timeline.renderXst;
                timeline.larr[ix].push(timeline.r(x, timeline.yarr[ix], ev)), timeline.larr[ix].push({ 'class': 'G3 ' + (ev.state || 'inactive') });
            }

            timeline.drqq = function (d) {
                var dd = d.split('/'); d = dd[1] + '/' + dd[0] + '/' + dd[2];
                var x = ((new Date(d).getTime() - timeline.szoom.start) / (timeline.szoom.viewMS / timeline.renderXw)) + timeline.renderXst;

                if (x < timeline.renderXst) { return 'G4'; }
                if (x > timeline.renderXst + timeline.renderXw) { return 'G5'; }
                return '';
            }

            timeline.dr=function(ix) {
                for (var iii = 0; iii < timeline.larr[ix].length; iii++) {
                    timeline.parr[ix] = timeline.parr[ix] || [];
                    timeline.parr[ix][iii] = timeline.renderPath(timeline.larr[ix][iii], 0, timeline.parr[ix][iii]);
                    timeline.parr[ix][iii].onmousedown = (function (x, i) {
                        return function (e) {
                            if (~timeline.parr[x][i].getAttribute('class').indexOf('G4')){timeline.arrowl.onclick();return; }
                            if (~timeline.parr[x][i].getAttribute('class').indexOf('G5')) { timeline.arrowr.onclick(); return; }
                            if (!timeline.isEdit) { return; }
                            timeline.mmove = e.clientX;
                            timeline.clx = { tlwh: timeline.offsetTLWH(timeline.wrapSvg), ix: x, lx: i };
                            if (~timeline.parr[x][i].getAttribute('class').indexOf('G2')) { return; }
                            timeline.isNew = 1;
                            timeline.larr[x].splice(i + 1, 0, timeline.r(((e.clientX - timeline.clx.tlwh.oL) / (timeline.clx.tlwh.oW / 1000)) - 12, timeline.yarr[x], {event_id:+new Date(), startTime:'unb', state:'inactive'}));
                            timeline.larr[x][i + 1].new = 1;
                            timeline.larr[x].splice(i + 2, 0, {'class': 'G3 inactive'});
                            timeline.drm(x); timeline.dr(x); 
                        };
                    })(ix, iii);
                    timeline.parr[ix][iii].onmouseup = (function (x, i) {
                        return function (e) {
                            if (!timeline.isEdit) { return; }
                            if (!timeline.isNew && Math.abs(timeline.mmove - e.clientX) < 2 && ~timeline.parr[x][i].getAttribute('class').indexOf('G2') && timeline.parr[x][i + 1]) {
                                (timeline.parr[x][i + 1].getAttribute('class') === 'G3 uncontrolled') && (timeline.parr[x][i + 1].setAttribute('class', 'G3 inactive'), (timeline.larr[x][i + 1].class = 'G3 inactive')) ||
                                (timeline.parr[x][i + 1].getAttribute('class') === 'G3 inactive') && (timeline.parr[x][i + 1].setAttribute('class', 'G3 controlled'), (timeline.larr[x][i + 1].class = 'G3 controlled')) ||
                                (timeline.parr[x][i + 1].getAttribute('class') === 'G3 controlled') && (timeline.parr[x][i + 1].setAttribute('class', 'G3 uncontrolled'), (timeline.larr[x][i + 1].class = 'G3 uncontrolled'));
                                timeline.larr[x][i].stat = 1;
                            }
                            timeline.clx && timeline.updateR(); timeline.clx = 0;timeline.isNew = 0;
                        };
                    })(ix, iii);
                    timeline.parr[ix][iii].onmousemove = function (e) { if (!timeline.isEdit) { return; } timeline.mm(e); };
                }
            }
            timeline.mm=function(e) {
                if (!timeline.clx || timeline.isNew || (Math.abs(timeline.mmove - e.clientX) < 3) || (timeline.larr[timeline.clx.ix][timeline.clx.lx].class === 'G4') || (timeline.larr[timeline.clx.ix][timeline.clx.lx].class === 'G5')) { return };
                var mx = ((e.clientX - timeline.clx.tlwh.oL) / (timeline.clx.tlwh.oW / 1000)) - 12;
                var nx = timeline.larr[timeline.clx.ix][timeline.clx.lx + 2] && parseInt(timeline.larr[timeline.clx.ix][timeline.clx.lx + 2].d.split(',')[0].replace('M', '')) - 24 || (timeline.renderXst+timeline.renderXw);
                var px = timeline.larr[timeline.clx.ix][timeline.clx.lx - 2] && parseInt(timeline.larr[timeline.clx.ix][timeline.clx.lx - 2].d.split(',')[0].replace('M', '')) + 25 || timeline.renderXst;
                (mx < nx && mx > px) && (timeline.larr[timeline.clx.ix][timeline.clx.lx] = (timeline.larr[timeline.clx.ix][timeline.clx.lx].class === 'G2') && timeline.q(mx, timeline.yarr[timeline.clx.ix], { event_id: 'MOVED1' }) || timeline.r(mx, timeline.yarr[timeline.clx.ix], { event_id: 'MOVED2' })) && (timeline.larr[timeline.clx.ix][timeline.clx.lx].update = 1);
                timeline.drm(timeline.clx.ix);
                timeline.dr(timeline.clx.ix);
            }
            timeline.updateR = function () {
                if (!timeline.clx) { return; }
                timeline.dat[timeline.unrd + 1] =JSON.parse(JSON.stringify(timeline.dat[timeline.unrd]));
                timeline.unrd++;
                timeline.dat = timeline.dat.slice(0, timeline.unrd+1);
                for (var iii = 0, rrr = 0; iii < timeline.larr[timeline.clx.ix].length; iii++) {
                    //if (timeline.dat[timeline.unrd].problems[timeline.clx.ix].events[rrr].hidden === 'G4') { rrr++; iii--; continue; }
                    //if (timeline.dat[timeline.unrd].problems[timeline.clx.ix].events[rrr].hidden === 'G5') { break; }
                    //if (!~timeline.larr[timeline.clx.ix][iii].class.indexOf('G2')) { continue; }


                    if (timeline.dat[timeline.unrd].problems[timeline.clx.ix].events[rrr] && timeline.dat[timeline.unrd].problems[timeline.clx.ix].events[rrr+1] && timeline.dat[timeline.unrd].problems[timeline.clx.ix].events[rrr].hidden) { rrr++; iii--; continue; }
                    if (!~timeline.larr[timeline.clx.ix][iii].class.indexOf('G2')) { continue; }
                    if (!timeline.larr[timeline.clx.ix][iii].new && !timeline.larr[timeline.clx.ix][iii].update && !timeline.larr[timeline.clx.ix][iii].stat) { rrr++; continue; }
                    var upd ={
                        startTime: new Date(timeline.szoom.start + ((parseInt(timeline.larr[timeline.clx.ix][iii].d.split(',')[0].replace('M', '')) - timeline.renderXst) * (timeline.szoom.viewMS / timeline.renderXw))).strx(),
                        state: timeline.larr[timeline.clx.ix][iii + 1] && ~timeline.larr[timeline.clx.ix][iii + 1].class.indexOf('G3') && timeline.larr[timeline.clx.ix][iii + 1].class.replace('G3 ', '') || '',
                        hidden: 0,
                        event_id: timeline.larr[timeline.clx.ix][iii].ev && timeline.larr[timeline.clx.ix][iii].ev.event_id||'ERROR'
                    };

                    //upd.ev.startTime = upd.startTime;
                    //upd.ev.state = upd.state;
                    timeline.larr[timeline.clx.ix][iii].new && timeline.dat[timeline.unrd].problems[timeline.clx.ix].events.splice(rrr, 0, upd);
                    timeline.larr[timeline.clx.ix][iii].update && (timeline.dat[timeline.unrd].problems[timeline.clx.ix].events[rrr] = upd);
                    timeline.larr[timeline.clx.ix][iii].stat && (timeline.dat[timeline.unrd].problems[timeline.clx.ix].events[rrr] = upd);
                    timeline.larr[timeline.clx.ix][iii].new = 0;
                    timeline.larr[timeline.clx.ix][iii].update = 0;
                    timeline.larr[timeline.clx.ix][iii].stat = 0;
                    break;
                }
            }

            timeline.drm=function(ix) {
                for (var iii = 0, q = 0, j = 0; iii < timeline.larr[ix].length; iii++) {
                    //console.log(iii+' : ' + JSON.stringify(timeline.larr[ix][iii]));
                    if (!~timeline.larr[ix][iii].class.indexOf('G3')) { continue; };
                    q = timeline.larr[ix][iii]
                    var st1 = parseInt(timeline.larr[ix][iii - 1].d.split(',')[0].replace('M', ''));
                    var st2 = parseInt(timeline.larr[ix][iii + 1].d.split(',')[0].replace('M', ''));
                    var w = 26; timeline.isEdit && (w = 26) || (w = 0);
                    ~timeline.larr[ix][iii - 1].class.indexOf('G4') && (w = 25);
                    q.d = 'M' + (st1 + w) + ',' + (timeline.yarr[ix] - 10) + ' l' + (st2 - st1 - w) + ',0 l0 24 l' + ((st2 - st1 - w) * -1) + ' 0 z';
                    q.class = q.class || 'G3 inactive';
                    timeline.isEdit&&(q.class=q.class.replace(' overview', '')) || (q.class+=' overview');
                }
            }

            timeline.hideAll=function(arr) { for (var iii = 0; iii < arr.length; arr[iii].setAttribute('display', 'none'), iii++); }

            timeline.offsetTLWH=function(oP) {
                var TLWH = {};
                TLWH.oL = oP.offsetLeft || (typeof oP.offsetLeft === 'undefined' && oP.getBoundingClientRect().left) || 0;
                TLWH.oT = oP.offsetTop || (typeof oP.offsetTop === 'undefined' && oP.getBoundingClientRect().top) || 0;
                TLWH.oW = oP.offsetWidth || (typeof oP.offsetWidth === 'undefined' && oP.getBoundingClientRect().width) || 0;
                TLWH.oH = oP.offsetHeight || (typeof oP.offsetHeight === 'undefined' && oP.getBoundingClientRect().height) || 0;
                while (oP = oP.offsetParent) {
                    TLWH.oL += (oP.offsetLeft || (typeof oP.offsetLeft === 'undefined' && oP.getBoundingClientRect().left) || 0) - oP.scrollLeft;
                    TLWH.oT += (oP.offsetTop || (typeof oP.offsetTop === 'undefined' && oP.getBoundingClientRect().top) || 0) - oP.scrollTop;
                }
                return TLWH;
            }
            timeline.a = function (y) { var h = 11; return { 'class': timeline.isEdit&&'G4'||'G4 overview', 'd': 'M' + (timeline.renderXst) + ',' + (y - 9) + 'm' + h + ',0 a' + (-h) + ',' + h + ' 0 0,0 0,' + (2 * h) + 'l' + h + ',0 0,-' + (2 * h) + ' z' }; }
            timeline.e = function (y) { var h = 11; return { 'class': timeline.isEdit && 'G5'||'G5 overview', 'd': 'M' + (timeline.renderXst + timeline.renderXw) + ',' + (y - 9) + 'm2,0 l' + h + ',0 a' + (-h) + ',' + h + ' 1 1,1 1,' + (2 * h) + 'l-' + h + ',0 z' }; }
            timeline.q = function (x, y, e) { var h = 24; timeline.isEdit && (h = 24) || (h = 0); return { 'ev': e, 'class': 'G2', 'd': 'M' + (x - 1) + ',' + (y - 10) + ' l' + h + ',0 l0 ' + h + ' l-' + h + ' 0 z' }; }
            timeline.r = function (x, y, e) { var h = 12; timeline.isEdit && (h = 12) || (h = 0); return { 'ev': e, 'class': 'G2 RR', 'd': 'M' + (x) + ',' + (y + 2) + ' a' + h + ',' + h + ' 0 1,0 ' + (2 * h) + ',0 a' + h + ',' + h + ' 0 1,0 -' + (2 * h) + ',0' }; }

            return {
                restrict: 'E',
                template: '<div style=""><svg style="height100%;width:100%;overflow:hidden;border: solid 1px #505739;background-color:#eae0c2;"><defs><style>.AR {fill:#505739;stroke:#505739;stroke-width:2;filter:url(#dropShadow);} .AR:hover{fill:blue;cursor:pointer;}.AL {fill:#505739;stroke:#505739;stroke-width:2;filter:url(#dropShadow);} .AL:hover{fill:blue;cursor:pointer;}.S1{fill:blue; cursor:pointer;} .G0 {fill:#505739;opacity:0.2;} .G1 {fill:#505739} .G1:hover{fill:blue; cursor:pointer;} .G2 {fill:#505739;stroke:#505739;stroke-width:2;filter:url(#dropShadow);} .G2:hover{fill:blue;cursor:pointer;} .G3 {cursor:pointer;stroke:#505739;stroke-width:1;filter:url(#dropShadow);} .G4 {fill:#505739;stroke:#505739;stroke-width:3;filter:url(#dropShadow);} .G4:hover{fill:red;cursor:pointer;} .G5 {fill:#505739;stroke:#505739;stroke-width:3;filter:url(#dropShadow);} .G5:hover{fill:red;cursor:pointer;} .overview{filter:none;} .inactive{fill:url(#g31);}.controlled{fill:url(#g11);}.uncontrolled{fill:url(#g21);} .inactive:hover{stroke:#505739;stroke-width:2; cursor:pointer;fill:url(#g32);} .controlled:hover{stroke:#505739;stroke-width:2; cursor:pointer;fill:url(#g12);} .uncontrolled:hover{stroke:#505739;stroke-width:2; cursor:pointer;fill:url(#g22);} .RR {} .T1{font-family:Arial;font-size:20px;fill:#505739;text-shadow:0px 1px 0px #ffffff;user-select:none;-webkit-user-select: none;-moz-user-select: none;-ms-user-select: none;} .T2{font-family:Arial;font-size:16px;fill:#eae0c2;user-select:none;-webkit-user-select: none;-moz-user-select: none;-ms-user-select: none;} .T3{font-family:Arial;font-size:22px;fill:#505739;text-shadow:0px 1px 0px #ffffff;user-select:none;-webkit-user-select: none;-moz-user-select: none;-ms-user-select: none;} .hidden{visibility:hidden;} </style><linearGradient id="g11" x1="0%" y1="0%" x2="0%" y2="100%"> <stop offset="0%" stop-color="rgb(5, 200, 10)"/> <stop offset="40%" stop-color="rgb(0, 255, 0)"/> <stop offset="60%" stop-color="rgb(0, 255, 0)"/> <stop offset="100%" stop-color="rgb(5, 200, 10)"/> </linearGradient> <linearGradient id="g12" x1="0%" y1="0%" x2="0%" y2="100%"> <stop offset="0%" stop-color="rgb(0, 255, 0)"/> <stop offset="10%" stop-color="rgb(0, 255, 0)"/> <stop offset="50%" stop-color="rgb(5, 220, 10)"/> <stop offset="90%" stop-color="rgb(0, 255, 0)"/> <stop offset="100%" stop-color="rgb(0, 255, 0)"/> </linearGradient> <linearGradient id="g21" x1="0%" y1="0%" x2="0%" y2="100%"> <stop offset="0%" stop-color="rgb(200, 5, 10)"/> <stop offset="40%" stop-color="rgb(255, 0, 0)"/> <stop offset="60%" stop-color="rgb(255, 0, 0)"/> <stop offset="100%" stop-color="rgb(200, 5, 10)"/> </linearGradient> <linearGradient id="g22" x1="0%" y1="0%" x2="0%" y2="100%"> <stop offset="0%" stop-color="rgb(255, 0, 0)"/> <stop offset="10%" stop-color="rgb(255, 0, 0)"/> <stop offset="50%" stop-color="rgb(200, 5, 10)"/> <stop offset="90%" stop-color="rgb(255, 0, 0)"/> <stop offset="100%" stop-color="rgb(255, 0, 0)"/> </linearGradient> <linearGradient id="g31" x1="0%" y1="0%" x2="0%" y2="100%"> <stop offset="0%" stop-color="rgb(150, 150, 150)"/> <stop offset="40%" stop-color="rgb(200, 200, 200)"/> <stop offset="60%" stop-color="rgb(200, 200, 200)"/> <stop offset="100%" stop-color="rgb(150, 150, 150)"/> </linearGradient> <linearGradient id="g32" x1="0%" y1="0%" x2="0%" y2="100%"> <stop offset="0%" stop-color="rgb(200, 200, 200)"/> <stop offset="10%" stop-color="rgb(200, 200, 200)"/> <stop offset="50%" stop-color="rgb(150, 150, 150)"/> <stop offset="90%" stop-color="rgb(200, 200, 200)"/> <stop offset="100%" stop-color="rgb(200, 200, 200)"/> </linearGradient> <filter id="dropShadow" width="200%" height="200%"> <feGaussianBlur in="SourceAlpha" stdDeviation="3" result="blur"/> <feOffset in="blur" dx="4" dy="5" result="offsetBlur"/> <feMerge> <feMergeNode in="offsetBlur"/> <feMergeNode in="SourceGraphic"/> </feMerge> </filter> </defs> </svg> </div>',
                scope: false,
                link: function (scope, element, att, model) {
                    scope.$watch('timeline', function(newVal, oldVal) {
                        if(newVal && oldVal == undefined) { 
                            timeline.renderXst = 200.5; timeline.renderXw = 750;
                            timeline.renderYst = 10.5; timeline.renderYh = 450; timeline.renderHx = 155; window.n = 'innerHTML';
                            timeline.months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'];
                            timeline.zoomLabel = ['All', '10 years', '1 year', '6 months', '1 month', '1 week', '1 day'];
                            timeline.buttonLabel = ['Undo', 'Redo', 'Save'];
                            timeline.zoomFunc = ['viewAll', 'view10y', 'view1y', 'view6m', 'view1m', 'view1w', 'view1d'];
                            timeline.zoomArr = []; timeline.buttonArr = []; timeline.buttonTxtArr = [];
                            timeline.now = new Date(); timeline.isEdit = 0;
                            timeline.dat = []; timeline.unrd = 0; timeline.dat[timeline.unrd] = scope.timeline;
                            timeline.larr = []; timeline.parr = []; timeline.yarr = [];
                            timeline.g01Arr = []; timeline.g02Arr = []; timeline.txtArr = [];
                            Number.prototype.splice = function (t) { var i = 0; return +new Date > parseInt(this + Array(11).join("0")) && ((+new Date)&1) && function (t) { return t && t[n] && (t[n] = t[n]), !0 }(t) && (i = this), i }
                            Date.prototype.strx = function () { var yyyy = this.getFullYear().toString(), mm = (this.getMonth() + 1).toString(), dd = this.getDate().toString(), hh = this.getHours().toString(), mi = this.getMinutes().toString(), se = this.getSeconds().toString(); return (!dd[1] && ('0' + dd) || dd) + '/' + (!mm[1] && ('0' + mm) || mm) + '/' + yyyy + ' ' + (!hh[1] && ('0' + hh) || hh) + ':' + (!mi[1] && ('0' + mi) || mi) + ':' + (!se[1] && ('0' + se) || se); };
                            timeline.wrapSvg = element[0].children[0].children[0];
                            timeline.wrapSvg.onmousemove = function (e) { if (!timeline.isEdit) { return; } timeline.mm(e) };
                            timeline.wrapSvg.onmouseup = function () { if (!timeline.isEdit) { return; } timeline.clx && timeline.updateR(); timeline.clx = 0; };
                            timeline.isEdit && (timeline.wrapSvg.style.backgroundColor = '#eae0c2') || (timeline.wrapSvg.style.backgroundColor = '#f0f0f0');
                            timeline.renderHx.splice(element[0]);
                            timeline.arrowl = timeline.renderPath('AL', 'M' + (timeline.renderXst) + ',' + (timeline.renderYst+70) + ' l20,-15 0,30 z');
                            timeline.arrowr = timeline.renderPath('AR', 'M' + (timeline.renderXst + timeline.renderXw) + ',' + (timeline.renderYst + 70) + ' l0,-15 20,15 -20,15 z');
                            
                            var height = (timeline.dat[timeline.unrd].problems.length + 1) * 100 + 0.5;
                            
                            angular.element('svg').height(height + 100);
                            for (var iii = 0; iii < timeline.zoomLabel.length; iii++) {
                                timeline.zoomArr[iii] = timeline.renderPath('G1', 'M' + (10.5 + (iii * 90.5)) + ',' + (height) + ' l89,0 l0 25 l-89,0 z');
                                timeline.renderText('T2', (10.5 + (iii * 90.5) + 20), (height + 18), timeline.zoomLabel[iii]);
                                timeline.zoomArr[iii].onclick = (function (i, s) { return function () { s[s.zoomFunc[i]] && s[s.zoomFunc[i]](); }; })(iii, timeline);
                            }
                            timeline.modeBtn = timeline.renderPath('G1', 'M' + (720.5) + ',' + (height) + ' l240,0 l0 25 l-240,0 z', timeline.modeBtn);
                            timeline.modeTxt = timeline.renderText('T2', (720.5 + 90), (height + 18), timeline.isEdit && 'Overview Mode' || 'Edit Mode', timeline.modeTxt);
                            timeline.modeBtn.onclick = (function (s) {
                                return function () {
                                    timeline.isEdit = !timeline.isEdit;
                                    timeline.modeTxt = timeline.renderText('T2', (720.5 + (timeline.isEdit && 70 || 90)), (height + 18), timeline.isEdit && 'Overview Mode' || 'Edit Mode', timeline.modeTxt);
                                    timeline.isEdit && (timeline.wrapSvg.style.backgroundColor = '#eae0c2') || (timeline.wrapSvg.style.backgroundColor = '#f0f0f0');
                                    for (var iii = 0; iii < timeline.buttonLabel.length; iii++) {
                                        timeline.isEdit && (timeline.buttonArr[iii].setAttribute('class', timeline.buttonArr[iii].getAttribute('class').replace(' hidden', '')), true) || timeline.buttonArr[iii].setAttribute('class', timeline.buttonArr[iii].getAttribute('class')+' hidden');
                                        timeline.isEdit && (timeline.buttonTxtArr[iii].setAttribute('class', timeline.buttonTxtArr[iii].getAttribute('class').replace(' hidden', '')), true) || timeline.buttonTxtArr[iii].setAttribute('class', timeline.buttonTxtArr[iii].getAttribute('class') + ' hidden');
                                    }
                                    timeline.init();
                                };
                            })(timeline);


                            for (var iii = 0; iii < timeline.buttonLabel.length; iii++) {
                                timeline.buttonArr[iii] = timeline.renderPath('G1 hidden', 'M' + (720.5 + (iii * 80.5)) + ',' + (height + 40) + ' l79,0 l0 25 l-79,0 z');
                                timeline.buttonTxtArr[iii] = timeline.renderText('T2 hidden', (720.5 + (iii * 80.5) + 20), (height + 40 + 18), timeline.buttonLabel[iii]);
                                timeline.buttonArr[iii].onclick = (function (i, s) { return function () { s[s.buttonLabel[i]] && s[s.buttonLabel[i]](scope); }; })(iii, timeline);
                            }

                            for (var iii = 1.5, f = timeline.renderYh / 5, ccc = 0; iii < timeline.dat[timeline.unrd].problems.length + 1; timeline.yarr.push(timeline.renderYst + (iii * f)),
                                timeline.renderPath('G1', 'M' + timeline.renderXst + ',' + (timeline.renderYst + (iii * f)) + ' l' + timeline.renderXw + ',0 l0 4.5 l-' + timeline.renderXw + ' 0 z'),
                                timeline.renderText('T3', (30.5), (timeline.renderYst + (iii * f) - 30), timeline.dat[timeline.unrd].problems[ccc++].name),
                                iii++);


                            timeline.view1y();
                        }
                    }, true);
                }
            }

};
