from rest_framework import serializers

from document_app.operations import fetch_document_label_set
from emr.models import Document, DocumentProblem, DocumentTodo
from problems_app.serializers import ProblemSerializer
from todo_app.serializers import TodoSerializer, LabelSerializer
from users_app.serializers import UserProfileSerializer


class DocumentListSerialization(serializers.ModelSerializer):
    patient = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            'id',
            'document_name',
            'patient',
        )

    def get_patient(self, obj):
        return obj.patient_id is None and " " or str(obj.patient)


class DocumentSerialization(serializers.ModelSerializer):
    author = UserProfileSerializer()
    patient = UserProfileSerializer()
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
