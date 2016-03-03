from rest_framework import serializers

from emr.models import ToDo, ToDoComment, Label, ToDoAttachment, TodoActivity

from problems_app.serializers import ProblemSerializer
from users_app.serializers import SafeUserSerializer, UserProfileSerializer


class LabelSerializer(serializers.ModelSerializer):

	class Meta:
		model = Label
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
			'filename',
			'is_image',
			)


class TodoSerializer(serializers.ModelSerializer):

	labels = LabelSerializer(many=True)
	comments = CommentToDoSerializer(many=True)
	attachments = AttachmentToDoSerializer(many=True)
	problem = ProblemSerializer()
	members = UserProfileSerializer(many=True)

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
			'members',
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

class TodoActivitySerializer(serializers.ModelSerializer):

	todo = TodoSerializer()
	author = UserProfileSerializer()
	comment = CommentToDoSerializer()
	attachment = AttachmentToDoSerializer()

	class Meta:
		model = TodoActivity

		fields = (
			'todo',
			'author',
			'activity',
			'comment',
			'attachment',
			'created_on')
