(function () {

    'use strict';

    angular.module('ManagerApp')
        .controller('TodoCtrl', TodoCtrl);
    TodoCtrl.$inject = ['$scope', '$routeParams', '$interval', 'patientService', 'ngDialog', 'todoService', 'toaster', 'sharedService', 'LABELS'];

    /**
     *
     * @param $scope
     * @param $routeParams
     * @param $interval
     * @param patientService
     * @param ngDialog
     * @param todoService
     * @param toaster
     * @param sharedService
     * @param LABELS
     * @constructor
     */
    function TodoCtrl($scope, $routeParams, $interval, patientService, ngDialog, todoService, toaster, sharedService, LABELS) {

        $scope.loading = true;
        $scope.todo_id = $routeParams.todo_id;
        $scope.current_activity = 0;
        $scope.labels_component = LABELS;
        $scope.label_component = {};
        $scope.allowDueDateNotification = true;
        $scope.new_comment = {
            comment: ""
        };

        $scope.isDueDate = isDueDate;
        $scope.add_comment = addComment;
        $scope.toggleEditComment = toggleEditComment;
        $scope.toggleSaveComment = toggleSaveComment;
        $scope.delete = deleteComment;
        $scope.confirmDelete = confirmDelete;
        $scope.changeText = changeText;
        $scope.saveTodoText = saveTodoText;
        $scope.updateTodoStatus = updateTodoStatus;
        $scope.createLabel = createLabel;
        $scope.createLabel2 = createLabel2;
        $scope.selectLabelComponent = selectLabelComponent;
        $scope.saveCreateLabel = saveCreateLabel;
        $scope.saveCreateLabelAll = saveCreateLabelAll;
        $scope.editLabel = editLabel;
        $scope.selectEditLabelComponent = selectEditLabelComponent;
        $scope.saveEditLabel = saveEditLabel;
        $scope.deleteEditLabel = deleteEditLabel;
        $scope.confirmDeleteLabel = confirmDeleteLabel;
        $scope.changeLabel = changeLabel;
        $scope.changeLabel2 = changeLabel2;
        $scope.changeTodoLabel = changeTodoLabel;
        $scope.changeDueDate = changeDueDate;
        $scope.changeDueDate2 = changeDueDate2;
        $scope.saveTodoDueDate = saveTodoDueDate;
        $scope.changeAttachment = changeAttachment;
        $scope.addAttachment = addAttachment;
        $scope.deleteAttachment = deleteAttachment;
        $scope.confirmDeleteAttachment = confirmDeleteAttachment;
        $scope.changeMember = changeMember;
        $scope.changeMember2 = changeMember2;
        $scope.changeTodoMember = changeTodoMember;
        $scope.refresh_todo_activity = refreshTodoActivity;
        $scope.isInArray = isInArray;
        $scope.checkSharedProblem = checkSharedProblem;
        $scope.deleteDocumentTag = deleteDocumentTag;
        $scope.deleteDocument = deleteDocument;
        $scope.removeMember = removeMember;

        init();

        $scope.$on('$destroy', () => {
            patientService.updateTodoCallback($scope.todo);
        });

        function init() {
            todoService.fetchTodoInfo($scope.todo_id).then(function (data) {
                $scope.todo = data['info'];
                $scope.comments = data['comments'];
                $scope.attachments = data['attachments'];
                $scope.documents = data['documents'];
                $scope.related_encounters = data['related_encounters'];
                $scope.activities = data['activities'];
                if (data['activities'].length) {
                    $scope.current_activity = data['activities'][0].id;
                }
                $interval(function () {
                    $scope.refresh_todo_activity();
                }, 10000);

                $scope.sharing_patients = data['sharing_patients'];
                $scope.loading = false;
            });

            todoService.addTodoAccessEncounter($scope.todo_id).then(function () {
            });

            todoService.fetchTodoMembers($scope.patient_id).then(function (data) {
                $scope.members = data['members'];
            });

            todoService.fetchLabels($scope.patient_id).then(function (data) {
                $scope.labels = data['labels'];
            });
        }

        function isDueDate(date) {
            var date = new Date(date);
            var today = new Date();
            if (date < today) {
                return 'due-date';
            }
            return '';
        }

        function addComment(form) {
            if (_.isEmpty(form.comment)) {
                return;
            }

            form.todo_id = $scope.todo_id;
            todoService.addComment(form).then((data) => {
                $scope.comments.push(data.comment);
                $scope.new_comment.comment = "";

                toaster.pop('success', 'Done', 'New Comment added successfully');
                // Asking for tag member
                ngDialog.open({
                    template: "postTodoCommentDialog",
                    showClose: false,
                    closeByNavigation: true,
                    scope: $scope,
                    controller: function () {
                        var vm = this;
                        vm.memberList = $scope.members;
                        vm.taggedMembers = _.map($scope.todo.members, (member) => {
                            return member.id
                        });
                        vm.memberSearch = "";

                        vm.toggleTaggedMember = toggleTaggedMember;
                        vm.memberFilter = memberFilter;

                        function memberFilter(item) {
                            return item.user.first_name.indexOf(vm.memberSearch) !== -1 || item.user.last_name.indexOf(vm.memberSearch) !== -1;
                        }

                        function toggleTaggedMember(event, member) {
                            let idx = vm.taggedMembers.indexOf(member.id);
                            idx === -1 ? vm.taggedMembers.push(member.id) : vm.taggedMembers.splice(idx, 1);

                            // Refocus on the search box to enable enter to submit
                            $(event.target.form).find('#member-searchbox').focus();
                        }
                    },
                    controllerAs: 'vm'
                }).closePromise.then((response) => {
                    // Calling tagged members service. Produce new list of members who will be tagged into this todo
                    if (!_.isUndefined(response.value) && "$escape" !== response.value && "$document" !== response.value) {
                        var originMembers = angular.copy($scope.todo.members);
                        var originalMembersID = _.map(originMembers, (member) => member.id);

                        _.each(originMembers, (member, memberIdx) => {
                            // Member exist in original but does not exist in new member list -> remove that member
                            if (response.value.indexOf(member.id) === -1) {
                                removeMember($scope.todo, member, memberIdx, false);
                            }
                        });

                        _.each(response.value, (memberID) => {
                            // Member exist in new member list but does not exist in the old member list -> add that member
                            if (originalMembersID.indexOf(memberID) === -1) {
                                let member = _.find($scope.members, (member) => member.id === memberID);
                                addMember($scope.todo, member, false);
                            }
                        });
                    }
                });

            });
        }

        function toggleEditComment(comment) {
            comment.edit = true;
        }

        function toggleSaveComment(comment) {

            todoService.editComment(comment).then(function (data) {
                comment.datetime = data['comment']['datetime'];
                comment.edit = false;
                toaster.pop('success', 'Done', 'Edited comment successfully');
            });

        }

        function deleteComment(comment) {
            $scope.currentComment = comment;
            angular.element('#deleteCommentModal').modal();
        }

        function confirmDelete(currentComment) {
            todoService.deleteComment(currentComment).then(function (data) {
                var index = $scope.comments.indexOf(currentComment);
                $scope.comments.splice(index, 1);
                angular.element('#deleteCommentModal').modal('hide');
                toaster.pop('success', 'Done', 'Deleted comment successfully');
            });
        }

        function changeText(todo) {
            todo.change_text = (todo.change_text != true) ? true : false;
        }

        function saveTodoText(todo) {
            todoService.changeTodoText(todo).then(function (data) {
                if (data['success']) {
                    todo.change_text = false;
                    toaster.pop('success', "Done", "Updated Todo text!");

                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });
        }

        function updateTodoStatus(todo) {
            // Don't show confirmation popup if change status from accomplished to true.
            // Because default ui checkbox behaviour the todo's accomplished status will be updated before confirm popup display
            // so we have to used todo's accomplished value changed already in frontend at this point
            if (_.contains(sharedService.settings.todo_popup_confirm, $scope.active_user.role) && $scope.todo.accomplished) {
                var confirmationPopup = ngDialog.open({
                    template: 'todoPopupConfirmDialog',
                    showClose: false,
                    closeByEscape: false,
                    closeByDocument: false,
                    closeByNavigation: false
                });

                confirmationPopup.closePromise.then(function (response) {
                    if (response.value) {
                        acceptedChangeTodoStatus();
                    } else {
                        // revert back to original todo's accomplished status due to non customized checkbox
                        $scope.todo.accomplished = !$scope.todo.accomplished;
                    }
                })
            } else {
                acceptedChangeTodoStatus()
            }

            function acceptedChangeTodoStatus(response) {

                patientService.updateTodoStatus(todo).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', "Done", "Updated Todo status !");
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                });
            }
        }

        function createLabel(todo) {
            todo.create_label = (todo.create_label != true) ? true : false;
        }

        function createLabel2(todo) {
            todo.create_label2 = (todo.create_label2 != true) ? true : false;
        }

        function selectLabelComponent(component) {
            $scope.label_component.css_class = component.css_class;
        }

        function saveCreateLabel(todo) {
            $scope.label_component.is_all = null;
            if ($scope.label_component.css_class != null) {
                todoService.saveCreateLabel(todo.id, $scope.label_component).then(function (data) {
                    if (data['success'] == true) {
                        if (data['new_status'] == true) {
                            $scope.labels.push(data['new_label']);
                        }
                        if (data['status'] == true) {
                            todo.labels.push(data['label']);
                            toaster.pop('success', "Done", "Added Todo label!");
                        }
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                });
            }
            todo.create_label = false;
            todo.create_label2 = false;
        }

        function saveCreateLabelAll(todo) {
            $scope.label_component.is_all = true;
            if ($scope.label_component.css_class != null) {
                todoService.saveCreateLabel(todo.id, $scope.label_component).then(function (data) {
                    if (data['success'] == true) {
                        if (data['new_status'] == true) {
                            $scope.labels.push(data['new_label']);
                        }
                        if (data['status'] == true) {
                            todo.labels.push(data['label']);
                            toaster.pop('success', "Done", "Added Todo label!");
                        }
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                });
            }
            todo.create_label = false;
            todo.create_label2 = false;
        }

        function editLabel(label) {
            label.edit_label = (label.edit_label != true) ? true : false;
        }

        function selectEditLabelComponent(label, component) {
            label.css_class = component.css_class;
        }

        function saveEditLabel(label) {
            if (label.css_class != null) {
                todoService.saveEditLabel(label).then(function (data) {
                    if (data['success'] == true) {
                        label.css_class = data['label']['css_class'];
                        if (data['status'] == true) {
                            angular.forEach($scope.todo.labels, function (value, key2) {
                                if (value.id == label.id) {
                                    value.css_class = label.css_class;
                                }
                            });
                            toaster.pop('success', "Done", "Changed label!");
                        }
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                });
            }
            label.edit_label = false;
        }

        function deleteEditLabel(label) {
            $scope.currentLabel = label;
            angular.element('#deleteLabelModal').modal();
        }

        function confirmDeleteLabel(currentLabel) {
            todoService.deleteLabel(currentLabel).then(function (data) {
                var index = $scope.labels.indexOf(currentLabel);
                $scope.labels.splice(index, 1);
                var index2;
                angular.forEach($scope.todo.labels, function (value, key) {
                    if (value.id == currentLabel.id) {
                        index2 = key;
                    }
                });
                if (index2 != undefined)
                    $scope.todo.labels.splice(index2, 1);
                angular.element('#deleteLabelModal').modal('hide');
                toaster.pop('success', 'Done', 'Deleted label successfully');
            });
        }

        function changeLabel(todo) {
            todo.change_label = (todo.change_label != true) ? true : false;
        }

        function changeLabel2(todo) {
            todo.change_label2 = (todo.change_label2 != true) ? true : false;
        }

        function changeTodoLabel(todo, label) {

            var is_existed = false;
            var existed_key;
            var existed_id;

            angular.forEach(todo.labels, function (value, key) {
                if (value.id == label.id) {
                    is_existed = true;
                    existed_key = key;
                    existed_id = value.id;
                }
            });
            if (!is_existed) {
                todo.labels.push(label);
                todoService.addTodoLabel(label.id, todo.id).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', "Done", "Added Todo label!");
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            } else {
                todo.labels.splice(existed_key, 1);
                todoService.removeTodoLabel(existed_id, todo.id).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', "Done", "Removed Todo label!");
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            }

        }

        function changeDueDate(todo) {
            todo.change_due_date = (todo.change_due_date != true) ? true : false;
        }

        function changeDueDate2(todo) {
            todo.change_due_date2 = (todo.change_due_date2 != true) ? true : false;
        }

        function saveTodoDueDate(todo) {
            todoService.changeTodoDueDate(todo).then(function (data) {
                if (data['success'] == true) {
                    if ($scope.allowDueDateNotification)
                        toaster.pop('success', "Done", "Due date Updated!");
                    $scope.allowDueDateNotification = true;
                } else if (data['success'] == false) {
                    todo.due_date = data['todo']['due_date'];
                    toaster.pop('error', 'Error', 'Invalid date format');
                    $scope.allowDueDateNotification = false;
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
            });
        }

        function changeAttachment(todo) {
            todo.change_attachment = (todo.change_attachment != true) ? true : false;
        }

        function addAttachment(todo, attachment) {
            var form = {};
            form.todo_id = $scope.todo_id;

            todoService.addAttachment(form, attachment).then(function (data) {
                if (data['success'] == true) {
                    toaster.pop('success', 'Done', 'Attachment uploaded!');
                    var attachment = data['attachment'];
                    console.log($scope.attachments);
                    $scope.attachments.push(attachment);
                } else if (data['success'] == false) {
                    toaster.pop('error', 'Error', 'Please fill valid data');
                } else {
                    toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                }
                todo.change_attachment = false
            });
        }

        function deleteAttachment(attachment) {
            $scope.currentAttachment = attachment;
            angular.element('#deleteAttachmentModal').modal();
        }

        function confirmDeleteAttachment(currentAttachment) {
            todoService.deleteAttachment(currentAttachment).then(function (data) {
                var index = $scope.attachments.indexOf(currentAttachment);
                $scope.attachments.splice(index, 1);
                angular.element('#deleteAttachmentModal').modal('hide');
                toaster.pop('success', 'Done', 'Deleted attachment successfully');
            });
        }

        function changeMember(todo) {
            todo.change_member = (todo.change_member != true) ? true : false;
        }

        function changeMember2(todo) {
            todo.change_member2 = (todo.change_member2 != true) ? true : false;
        }

        function changeTodoMember(todo, member) {

            var is_existed = false;
            var existed_key;
            var existed_id;

            angular.forEach(todo.members, function (value, key) {
                if (value.id === member.id) {
                    is_existed = true;
                    existed_key = key;
                    existed_id = value.id;
                }
            });
            if (!is_existed) {
                addMember(todo, member);
            } else {
                removeMember(todo, member, existed_key);
            }

        }

        function refreshTodoActivity() {
            todoService.getTodoActivity($scope.todo_id, $scope.current_activity).then(function (data) {
                if (data != null) {
                    if (data['activities'].length) {
                        for (var i = data['activities'].length - 1; i >= 0; i--) {
                            $scope.activities.unshift(data['activities'][i]);
                        }
                        $scope.current_activity = data['activities'][0].id;
                    }
                }
            })
        }

        function isInArray(array, item) {
            var is_existed = false;
            angular.forEach(array, function (value, key2) {
                if (value == item) {
                    is_existed = true;
                }
            });
            return is_existed;
        }

        /**
         * TODO: Active user is not finished fetching
         * @param problem
         * @param sharing_patients
         * @returns {boolean}
         */
        function checkSharedProblem(problem, sharing_patients) {
            if ($scope.patient_id == $scope.user_id || ($scope.active_user && $scope.active_user.role != 'patient')) {
                return true;
            } else {
                var is_existed = false;
                angular.forEach(sharing_patients, function (p, key) {
                    if (!is_existed && p.user.id == $scope.user_id) {
                        is_existed = $scope.isInArray(p.problems, problem.id);
                    }
                });

                return is_existed;
            }
        }

        function deleteDocumentTag(document, todo) {
            ngDialog.openConfirm({
                template: 'delete-document-tag',
                showClose: false
            }).then(function (success) {
                if (_.contains(['physician', 'admin'], $scope.active_user.role)) {
                    // Asking for delete file from system or not
                    $scope.deleteDocument(document, todo);
                } else {
                    sharedService.deleteDocumentTag(document, todo, 'todo', false)
                        .then(function (success) {
                            toaster.pop('success', 'Done', 'Document remove successfully');
                        }, function (error) {
                            toaster.pop('error', 'Error', 'Document remove failed');
                        })
                }
            }, function (error) {
                console.log('user cancel');
            });
        }

        function deleteDocument(document, todo) {
            ngDialog.openConfirm({
                template: 'delete-document',
                showClose: false
            }).then(function () {
                sharedService.deleteDocumentTag(document, todo, 'todo', true)
                    .then(function (success) {
                        toaster.pop('success', 'Done', 'Document remove successfully');
                    }, function (error) {
                        toaster.pop('error', 'Error', 'Document remove failed');
                    })
            }, function () {
                sharedService.deleteDocumentTag(document, todo, 'todo', false)
                    .then(function (success) {
                        toaster.pop('success', 'Done', 'Document remove successfully');
                    }, function (error) {
                        toaster.pop('error', 'Error', 'Document remove failed');
                    })
            });
        }

        function addMember(todo, member, showToast = true) {
            todo.members.push(member.user);
            todoService.addTodoMember(todo, member).then((data) => {
                if (showToast)
                    data.success ? toaster.pop('success', "Done", "Added member!") : toaster.pop('error', 'Warning', 'Something went wrong!');
            });
        }

        function removeMember(todo, member, memberIdx, showToast = true) {
            todo.members.splice(memberIdx, 1);
            todoService.removeTodoMember(todo, member).then((data) => {
                if (showToast)
                    data.success ? toaster.pop('success', "Done", "Removed member!") : toaster.pop('error', 'Warning', 'Something went wrong!');
            });
        }
    }
})();