from rest_framework import serializers

from emr.models import ToDo, ToDoComment, Label, ToDoAttachment, TodoActivity, LabeledToDoList
from users_app.serializers import SafeUserSerializer, UserProfileSerializer


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
    due_date = serializers.DateField(format='%m/%d/%Y')
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
    author = UserProfileSerializer()
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
