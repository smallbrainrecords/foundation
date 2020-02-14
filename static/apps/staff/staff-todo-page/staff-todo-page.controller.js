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


    angular.module('StaffApp')
        .controller('TodoCtrl', function ($scope, $routeParams, $interval, staffService, ngDialog, todoService, toaster) {

            $scope.user_id = $('#user_id').val();
            $scope.todo_id = $routeParams.todo_id;
            $scope.labels_component = [
                {name: 'green', css_class: 'todo-label-green'},
                {name: 'yellow', css_class: 'todo-label-yellow'},
                {name: 'orange', css_class: 'todo-label-orange'},
                {name: 'red', css_class: 'todo-label-red'},
                {name: 'purple', css_class: 'todo-label-purple'},
                {name: 'blue', css_class: 'todo-label-blue'},
                {name: 'sky', css_class: 'todo-label-sky'},
            ];
            $scope.current_activity = 0;
            $scope.label_component = {};
            $scope.new_comment = {
                comment: ""
            };
            $scope.activities = [];
            $scope.allowDueDateNotification = true;

            $scope.isDueDate = isDueDate;
            $scope.add_comment = add_comment;
            $scope.toggleEditComment = toggleEditComment;
            $scope.toggleSaveComment = toggleSaveComment;
            $scope.delete = deleteComment;
            $scope.confirmDelete = confirmDelete;
            $scope.changeText = changeText;
            $scope.saveTodoText = saveTodoText;
            $scope.update_todo_status = update_todo_status;
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
            $scope.refresh_todo_activity = refresh_todo_activity;

            init();

            function init() {
                todoService.fetchTodoInfo($scope.todo_id).then(function (data) {
                    $scope.todo = data['info'];
                    $scope.comments = data['comments'];
                    $scope.attachments = data['attachments'];
                    $scope.related_encounters = data['related_encounters'];
                    $scope.activities = data['activities'];
                });

                staffService.fetchActiveUser().then(function (data) {
                    $scope.active_user = data['user_profile'];
                });

                todoService.addTodoAccessEncounter($scope.todo_id).then(function () {
                });

                todoService.fetchTodoMembers($scope.user_id).then(function (data) {
                    $scope.members = data['members'];
                });

                todoService.fetchLabels($scope.user_id).then(function (data) {
                    $scope.labels = data['labels'];
                });

                $interval(function () {
                    $scope.refresh_todo_activity();
                }, 4000);
            }


            function isDueDate(date) {
                var date = new Date(date);
                var today = new Date();
                if (date < today) {
                    return 'due-date';
                }
                return '';
            }

            // add comment
            function add_comment(form) {
                form.todo_id = $scope.todo_id;

                todoService.addComment(form).then(function (data) {
                    var comment = data['comment'];
                    $scope.comments.push(comment);

                    $scope.new_comment.comment = "";
                    toaster.pop('success', 'Done', 'New Comment added successfully');
                });
            }

            // edit comment
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

            // delete comment
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

            // change todo text
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

            // update status
            function update_todo_status(todo) {
                todoService.updateTodoStatus(todo).then(function (data) {
                    if (data['success'] == true) {
                        toaster.pop('success', "Done", "Updated Todo status !");
                    } else {
                        toaster.pop('error', 'Warning', 'Something went wrong!');
                    }
                });

            }

            // change label
            // label


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

            // change due date
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
                        todo.change_due_date = !todo.change_due_date;
                    } else if (data['success'] == false) {
                        todo.due_date = data['todo']['due_date'];
                        toaster.pop('error', 'Error', 'Invalid date format');
                        $scope.allowDueDateNotification = false;
                    } else {
                        toaster.pop('error', 'Error', 'Something went wrong, we are fixing it asap!');
                    }
                });
            }

            // Attachment
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

            // delete Attachment
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

            // add member
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
                    if (value.id == member.id) {
                        is_existed = true;
                        existed_key = key;
                        existed_id = value.id;
                    }
                });
                if (!is_existed) {
                    todo.members.push(member);
                    todoService.addTodoMember(todo, member).then(function (data) {
                        if (data['success'] == true) {
                            toaster.pop('success', "Done", "Added member!");
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                } else {
                    todo.members.splice(existed_key, 1);
                    todoService.removeTodoMember(todo, member).then(function (data) {
                        if (data['success'] == true) {
                            toaster.pop('success', "Done", "Removed member!");
                        } else {
                            toaster.pop('error', 'Warning', 'Something went wrong!');
                        }
                    });
                }

            }

            function refresh_todo_activity() {
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


        });
    /* End of controller */


})();