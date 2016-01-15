from rest_framework import serializers


from emr.models import Problem, PatientImage, ProblemRelationship
from emr.models import ProblemNote, ProblemActivity, ProblemSegment

from users_app.serializers import UserProfileSerializer


class ProblemSegmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProblemSegment

        fields = (
            'id',
            'problem',
            'is_controlled',
            'is_active',
            'authenticated',
            'event_id',
            'start_time',
            'start_date',)


class ProblemSerializer(serializers.ModelSerializer):
    problem_segment = ProblemSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = Problem

        fields = (
            'id',
            'problem_segment',
            'patient',
            'parent',
            'problem_name',
            'concept_id',
            'is_controlled',
            'is_active',
            'authenticated',
            'start_time',
            'start_date',)


class PatientImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = PatientImage

        fields = (
            'id',
            'patient',
            'problem',
            'image',
            'datetime')


class ProblemRelationshipSerializer(serializers.ModelSerializer):

    source = ProblemSerializer()
    target = ProblemSerializer()

    class Meta:
        model = ProblemRelationship
        fields = (
            'id',
            'source',
            'target')


class ProblemNoteSerializer(serializers.ModelSerializer):

    author = UserProfileSerializer()

    class Meta:
        model = ProblemNote
        fields = (
            'author',
            'problem',
            'note',
            'note_type',
            'created_on')


class ProblemActivitySerializer(serializers.ModelSerializer):

    author = UserProfileSerializer()

    class Meta:
        model = ProblemActivity

        fields = (
            'author',
            'activity',
            'problem',
            'created_on')
