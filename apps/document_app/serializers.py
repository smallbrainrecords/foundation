from rest_framework import serializers
from emr.models import Document, DocumentProblem, DocumentTodo
from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer, LabelSerializer
from problems_app.serializers import ProblemSerializer


class DocumentSerialization(serializers.ModelSerializer):
    author = UserProfileSerializer()
    patient = UserProfileSerializer()
    labels = LabelSerializer(many=True)
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
            'filename',
            'file_mime_type',
            'created_on'
        )


class DocumentTodoSerialization(serializers.ModelSerializer):
    document = DocumentSerialization()
    todo = TodoSerializer()
    author = UserProfileSerializer()

    class Meta:
        model = DocumentTodo
        fields = (
            'document',
            'todo',
            'author',
        )


class DocumentProblemSerialization(serializers.ModelSerializer):
    document = DocumentSerialization()
    problem = ProblemSerializer()
    author = UserProfileSerializer()

    class Meta:
        model = DocumentProblem
        fields = (
            'document',
            'problem',
            'author',
        )
