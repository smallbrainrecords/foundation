from rest_framework import serializers



from emr.models import Goal


class GoalSerializer(serializers.ModelSerializer):

	class Meta:
		model = Goal
		fields = (
			'id',
			'patient', 
			'problem', 
			'goal', 
			'is_controlled',
			'accomplished',
			'start_date')
