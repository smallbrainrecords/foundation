from rest_framework import serializers


from emr.models import Problem, PatientImage, ProblemRelationship

class ProblemSerializer(serializers.ModelSerializer):

	class Meta:
		model = Problem

		fields = (
				'id',
				'patient',
				'parent',
				'problem_name',
				'concept_id',
				'is_controlled',
				'is_active',
				'authenticated',
				'start_date',
			)


class PatientImageSerializer(serializers.ModelSerializer):

	class Meta:
		model = PatientImage

		fields = (
			'id',
			'patient',
			'problem',
			'image',
			'datetime'
			)


class  ProblemRelationshipSerializer(serializers.ModelSerializer):

	source = ProblemSerializer()
	target = ProblemSerializer()
	
	class Meta:
		model = ProblemRelationship
		fields = (
				'id',
				'source',
				'target'
			)