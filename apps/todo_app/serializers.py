from rest_framework import serializers

from emr.models import ToDo




class TodoSerializer(serializers.ModelSerializer):


	class Meta:
		model = ToDo

		fields = (
			'id',
			'patient',
			'problem',
			'todo',
			'accomplished',
			)