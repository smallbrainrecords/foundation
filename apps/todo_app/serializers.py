from rest_framework import serializers

from emr.models import ToDo, ToDoComment

from problems_app.serializers import ProblemSerializer
from users_app.serializers import SafeUserSerializer


class TodoSerializer(serializers.ModelSerializer):


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