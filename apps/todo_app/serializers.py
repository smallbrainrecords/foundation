from rest_framework import serializers

from emr.models import ToDo, ToDoComment, ToDoLabel

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

class TodoSerializer(serializers.ModelSerializer):

	labels = ToDoLabelSerializer(many=True)
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