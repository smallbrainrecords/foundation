"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""

from rest_framework import serializers

from emr.models import ToDo, ToDoComment, Label, ToDoAttachment, TodoActivity, LabeledToDoList
from users_app.serializers import SafeUserSerializer


class LabelSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()

    class Meta:
        model = Label
        fields = (
            'id',
            'name',
            'css_class',
            'author',
            'is_all',
        )


class CommentToDoSerializer(serializers.ModelSerializer):
    user = SafeUserSerializer()

    class Meta:
        model = ToDoComment

        fields = (
            'id',
            'user',
            'comment',
            'datetime',
        )


class AttachmentToDoSerializer(serializers.ModelSerializer):
    user = SafeUserSerializer()

    class Meta:
        model = ToDoAttachment

        fields = (
            'id',
            'user',
            'attachment',
            'datetime',
            'filename',
            'is_image',
        )


class TodoSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True)
    comments = CommentToDoSerializer(many=True)
    attachments = AttachmentToDoSerializer(many=True)
    patient = SafeUserSerializer()
    members = SafeUserSerializer(many=True)
    due_date = serializers.DateTimeField(format='%m/%d/%Y')
    problem = serializers.SerializerMethodField()

    class Meta:
        model = ToDo

        fields = (
            'id',
            'patient',
            'user',
            'problem',
            'todo',
            'accomplished',
            'due_date',
            'labels',
            'comments',
            'attachments',
            'members',
            'document_set',
            'a1c',
            'colon_cancer',
            'created_at',
            'created_on',
        )

    def get_problem(self, obj):
        from problems_app.serializers import ProblemSerializer
        if obj.problem:
            return ProblemSerializer(obj.problem).data
        else:
            return None


class ToDoCommentSerializer(serializers.ModelSerializer):
    user = SafeUserSerializer()
    todo = TodoSerializer()

    class Meta:
        model = ToDoComment

        fields = (
            'id',
            'todo',
            'user',
            'comment',
            'datetime',
        )


class TodoActivitySerializer(serializers.ModelSerializer):
    todo = TodoSerializer()
    author = SafeUserSerializer()
    comment = CommentToDoSerializer()
    attachment = AttachmentToDoSerializer()

    class Meta:
        model = TodoActivity

        fields = (
            'id',
            'todo',
            'author',
            'activity',
            'comment',
            'attachment',
            'created_on')


class LabeledToDoListSerializer(serializers.ModelSerializer):
    user = SafeUserSerializer()
    labels = LabelSerializer(many=True)

    class Meta:
        model = LabeledToDoList

        fields = (
            'id',
            'user',
            'labels',
            'name')
