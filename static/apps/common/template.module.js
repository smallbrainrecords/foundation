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


    angular.module('TemplateCache', [])
        .run(function ($templateCache) {
            $templateCache.put('bleedingRiskDialog', "<div><p  class='text-center'>This patient is on Warfarin, will this affect the patient's bleeding risk?</p><div class='ngdialog-buttons text-right'><button class='btn btn-primary' ng-click='closeThisDialog()'>Thank you</button></div></div>");
            $templateCache.put('askDueDateDialog', '<div class="row" ng-keypress="$event.which === 13 && vm.dueDateIsValid() && closeThisDialog(vm.dueDate)"><div class="col-md-12"><p>Enter due date</p><input class="form-control" auto-focus type="text" ng-model="vm.dueDate" title="Due date" placeholder="Enter a due date"></div><div class="col-md-12 text-right ngdialog-buttons"><br><button class="btn btn-primary"  ng-click="vm.dueDateIsValid() && closeThisDialog(vm.dueDate)">Ok</button><button class="btn btn-danger" ng-click="closeThisDialog()">Add todo without a due date</button></div></div>');
            $templateCache.put('postAddTodoDialog', '<form ng-submit="closeThisDialog(vm.taggedMembers)" class="clearfix"><p>Tag member to this todo</p><input type="text" class="form-control member-search-box" ng-model="vm.memberSearch" title="Search members" placeholder="Search members"/><a ng-repeat="member in vm.memberList | filter : vm.memberFilter" class="member-tagging"   ng-click="vm.toggleTaggedMember(member,$event)"><span class="full-name">{{member.user.first_name}} {{member.user.last_name}}</span><i class="fa fa-check pull-right" ng-if="vm.taggedMembers.indexOf(member.id) != -1"></i></a><button class="btn btn-primary pull-right" type="submit">Submit</button></form>');
            $templateCache.put('postTodoCommentDialog', '<div class="dialog-contents"><form novalidate ng-submit="closeThisDialog(vm.taggedMembers)"><div class="row"><div class="col-md-12"><p>Tag members</p><input type="text" class="form-control member-search-box"ng-model="vm.memberSearch" title="Search members" id="member-searchbox" placeholder="Search members"/><button type="button" ng-repeat="member in vm.memberList | filter : vm.memberFilter" class="member-tagging" ng-click="vm.toggleTaggedMember($event,member)">{{member.user.first_name}} {{member.user.last_name}}<i class="fa fa-check pull-right" ng-if="vm.taggedMembers.indexOf(member.id) != -1"></i></button></div><div class="col-md-12 ngdialog-buttons text-right"><button class="btn btn-primary" type="submit">Done</button><button class="btn btn-danger" ng-click="closeThisDialog()">Don\'t tag anybody</button></div></div></form>');
            $templateCache.put('todoPopupConfirmDialog', "<div class='ngdialog-buttons text-right'><button class='btn btn-primary' ng-click='closeThisDialog(true)'>Yes, mark this todo as accomplished?</button> <button class='btn btn-danger' ng-click='closeThisDialog()'>No, don't mark this todo as accomplished</button></div>");
            $templateCache.put('documentConfirmDialog', "<div class='text-center'><p>This is a permanent deletion</p><div class='ngdialog-buttons text-right'><button class='btn btn-danger' ng-click='closeThisDialog(true)'>Yes delete</button><button class='btn btn-primary' ng-click='closeThisDialog(false)'>No do not delete</button></div></div>");
            $templateCache.put('reSubmitConfirmDialog', "<div><p  class='text-center'>You have already entered the vitals. Are you sure you want to enter them again</p><div class='ngdialog-buttons text-right'><button class='btn btn-danger' ng-click='confirm()'>Yes</button><button class='btn btn-primary' ng-click='closeThisDialog()'>No</button></div></div>");
            $templateCache.put('delete-document-tag', '<div class="dialog-contents text-center"><p>Remove this document from the todo only</p><div class="ngdialog-buttons"><button class="btn btn-danger" ng-click="confirm()">Confirm</button><button class="btn btn-primary" ng-click="closeThisDialog()">Cancle</button></div></div>');
            $templateCache.put('delete-document', '<div class="dialog-contents text-center"><p>Delete this document from the todo and the system</p><div class="ngdialog-buttons"><button class="btn btn-danger" ng-click="confirm()">Yes, delete from both</button><button class="btn btn-primary" ng-click="closeThisDialog()">No, only delete from todo</button></div></div>');
            $templateCache.put('portraitUpdateDialog', '<div class="dialog-contents text-center"><p>Update Profile Picture</p><div class="row align-center"><input type="file" class="hide" id="portrait-image-holder" accept="image/*" on-file-change="file_changed" name="portrait_image"><canvas id="snapshot" class="hide"></canvas><div class="col-xs-6 col-sm-6 col-md-6 col-log-6 btn-upload" onclick="$(\'#portrait-image-holder\').click();"><span class="glyphicon glyphicon-plus"></span> <span class="">Upload photo</span></div><div class="col-xs-6 col-sm-6 col-md-6 col-log-6 btn-take-photo" ng-click="reset_take_photo_flags()"><span class="glyphicon glyphicon-camera"></span> <span class="">Take Photo</span></div><div class="col-xs-12 col-sm-12 col md-12 col-lg-12"><div ng-if="get_image_via_camera_flag && !photo_is_taken_flag"><webcam channel="channel" on-access-denied="onError(err)" on-streaming="onSuccess()"></webcam><button type="button" class="btn btn-primary float-right" ng-click="take_snapshot()">Take photo</button></div><form ng-submit="submit_form()" class="align-center" ng-if="preview_image_src"><img ng-src="{{ preview_image_src }}" class="thumbnail thumbnail-custom preview-image"><button type="submit" class="btn btn-primary float-right">Save</button></form></div></div></div>');
            $templateCache.put('imageBoxDialog', '<div class="dialog-contents text-center"><img ng-src="{{image.image}}" class="thumbnail modal-image"></div>');
            $templateCache.put('labelDeleteConfirmationDialog', '<div class="dialog-contents text-center"><h4>Are you sure?</h4><p>Deleting a label is forever. There is no undo.</p><div class="ngdialog-buttons text-right"><button class="btn btn-danger" ng-click="confirmDeleteLabel(currentLabel)">Delete</button></div></div>');
            $templateCache.put('copyEncounterDialog', '<div class="dialog-contents text-center"><h2 ng-if="!vm.dataIsLoaded">Generating data</h2> <h2 ng-if="vm.dataIsLoaded">Data is ready</h2><div class="ngdialog-buttons text-center"><button ng-disabled="!vm.dataIsLoaded" type="button" ng-click="vm.copy(); closeThisDialog()" ng-keypress="$event.which === 13" class="btn btn-primary">Copy</button></div></div>');
        });
})();
