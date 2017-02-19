(function () {

    'use strict';


    angular.module('TemplateCache', [])
        .run(function ($templateCache) {
            $templateCache.put('bleedingRiskDialog',
                "<div class='text-center'><p>This patient is on Warfarin, will this affect the patient's bleeding risk?</p><button class='btn btn-primary' ng-click='closeThisDialog()'>Thank you</button></div>");
            $templateCache.put('askDueDateDialog',
                '<div class="row" ng-keypress="$event.which === 13 && vm.dueDateIsValid() && closeThisDialog(vm.dueDate)"><div class="col-md-12"><p>Enter due date</p><input class="form-control" auto-focus type="text" ng-model="vm.dueDate" title="Due date" placeholder="Enter a due date"></div><div class="col-md-12 text-right ngdialog-buttons"><br><button class="btn btn-primary"  ng-click="vm.dueDateIsValid() && closeThisDialog(vm.dueDate)">Ok</button><button class="btn btn-danger" ng-click="closeThisDialog()">Add todo without a due date</button></div></div>');
            $templateCache.put('todoPopupConfirmDialog',
                "<button class='btn btn-primary btn-block' ng-click='closeThisDialog(true)'>Yes, mark this todo as accomplished?</button> <button class='btn btn-danger btn-block' ng-click='closeThisDialog()'>No, don't mark this todo as accomplished</button>");
            $templateCache.put('documentConfirmDialog',
                "<div class='text-center'><p>This is a permanent deletion</p>" +
                "<button class='btn btn-danger' ng-click='closeThisDialog(true)'>Yes delete</button>" +
                "<button class='btn btn-primary' ng-click='closeThisDialog(false)'>No do not delete</button></div>");
        });
})();
