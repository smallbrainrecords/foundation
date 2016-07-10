from rest_framework import serializers

from emr.models import Observation, ObservationTextNote, ObservationComponent, ObservationComponentTextNote

from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer
from problems_app.serializers import ProblemSerializer


class ObservationTextNoteSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = ObservationTextNote
        fields = (
            'id',
            'author',
            'note',
            'datetime',
            )


class ObservationComponentTextNoteSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = ObservationComponentTextNote
        fields = (
            'id',
            'author',
            'note',
            'datetime',
            )


class ObservationComponentSerializer(serializers.ModelSerializer):
    observation_component_notes = ObservationComponentTextNoteSerializer(many=True, read_only=True)
    author = UserProfileSerializer()

    class Meta:
        model = ObservationComponent
        fields = (
            'id',
            'value_quantity',
            'effective_datetime',
            'created_on',
            'observation_component_notes',
            'author',
            )

class ObservationSerializer(serializers.ModelSerializer):
    subject = UserProfileSerializer()
    encounter = UserProfileSerializer()
    performer = UserProfileSerializer()
    author = UserProfileSerializer()
    problem = ProblemSerializer()
    observation_todos = TodoSerializer(many=True, read_only=True)
    observation_notes = ObservationTextNoteSerializer(many=True, read_only=True)
    observation_components = ObservationComponentSerializer(many=True, read_only=True)

    class Meta:
        model = Observation
        fields = (
            'id',
            'status',
            'category',
            'code',
            'subject',
            'encounter',
            'performer',
            'author',
            'problem',
            'effective_datetime',
            'value_quantity',
            'value_codeableconcept',
            'value_string',
            'value_unit',
            'comments',
            'created_on',
            'todo_past_six_months',
            'observation_todos',
            'observation_notes',
            'observation_components',
            'patient_refused_A1C',
            )