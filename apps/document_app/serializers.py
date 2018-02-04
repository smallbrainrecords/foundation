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

from document_app.operations import fetch_document_label_set
from emr.models import Document, DocumentProblem, DocumentTodo
from problems_app.serializers import ProblemSerializer
from todo_app.serializers import TodoSerializer, LabelSerializer
from users_app.serializers import SafeUserSerializer


class DocumentListSerializer(serializers.ModelSerializer):
    patient = SafeUserSerializer()

    class Meta:
        model = Document
        fields = (
            'id',
            'document_name',
            'patient',
        )


class DocumentSerializer(serializers.ModelSerializer):
    author = SafeUserSerializer()
    patient = SafeUserSerializer()
    labels = serializers.SerializerMethodField()
    todos = TodoSerializer(many=True)
    problems = ProblemSerializer(many=True)

    class Meta:
        model = Document
        fields = (
            'id',
            'author',
            'patient',
            'document',
            'labels',
            'todos',
            'problems',
            'document_name',
            'file_mime_type',
            'created_on'
        )

    def get_labels(self, obj):
        return LabelSerializer(fetch_document_label_set(obj), many=True).data


class DocumentTodoSerializer(serializers.ModelSerializer):
    document = DocumentSerializer()
    todo = TodoSerializer()
    author = SafeUserSerializer()

    class Meta:
        model = DocumentTodo
        fields = (
            'document',
            'todo',
            'author',
        )


class DocumentProblemSerializer(serializers.ModelSerializer):
    document = DocumentSerializer()
    problem = ProblemSerializer()
    author = SafeUserSerializer()

    class Meta:
        model = DocumentProblem
        fields = (
            'document',
            'problem',
            'author',
        )
