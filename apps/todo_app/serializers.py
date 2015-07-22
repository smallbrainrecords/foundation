from rest_framework import serializers

from emr.models import ToDo

from problems_app.serializers import ProblemSerializer


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
			)