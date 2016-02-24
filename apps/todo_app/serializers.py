from rest_framework import serializers

from emr.models import ToDo, ToDoComment, ToDoLabel, ToDoAttachment

from problems_app.serializers import ProblemSerializer
from users_app.serializers import SafeUserSerializer


class ToDoLabelSerializer(serializers.ModelSerializer):

	class Meta:
		model = ToDoLabel
		fields = (
			'id',
			'name',
			'css_class',
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
			)


class TodoSerializer(serializers.ModelSerializer):

	labels = ToDoLabelSerializer(many=True)
	comments = CommentToDoSerializer(many=True)
	attachments = AttachmentToDoSerializer(many=True)
	problem = ProblemSerializer()

	class Meta:
		model = ToDo

		fields = (
			'id',
			'patient',
			'problem',
			'todo',
			'accomplished',
			'due_date',
			'labels',
			'comments',
			'attachments',
			)


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