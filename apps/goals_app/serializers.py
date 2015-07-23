from rest_framework import serializers



from emr.models import Goal
from problems_app.serializers import ProblemSerializer

class GoalSerializer(serializers.ModelSerializer):


	problem = ProblemSerializer()
	
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
