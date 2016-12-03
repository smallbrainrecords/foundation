from rest_framework import serializers
from emr.models import Document, DocumentProblem, DocumentTodo
from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer
from problems_app.serializers import ProblemSerializer


class DocumentSerialization(serializers.ModelSerializer):
    author = UserProfileSerializer()
    patient = UserProfileSerializer()

    class Meta:
        model = Document
        fields = (
            'id',
            'author',
            'filename',
            'file_mime_type',
            'patient',
            'document',
            'created_on'
        )


class DocumentTodoSerialization(serializers.ModelSerializer):
    document = DocumentSerialization()
    todo = TodoSerializer()

    class Meta:
        model = DocumentTodo
        fields = (
            'document',
            'todo'
        )


class DocumentProblemSerialization(serializers.ModelSerializer):
    document = DocumentSerialization()
    problem = ProblemSerializer()

    class Meta:
        model = DocumentProblem
        fields = (
            'document',
            'problem'
        )
