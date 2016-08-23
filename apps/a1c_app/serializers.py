from rest_framework import serializers

from emr.models import Observation, AOneCTextNote, ObservationComponent, ObservationComponentTextNote, AOneC

from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer
from problems_app.serializers import ProblemSerializer


class AOneCTextNoteSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = AOneCTextNote
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
            'effective_datetime',
            'comments',
            'created_on',
            'observation_components',
            )

class AOneCSerializer(serializers.ModelSerializer):
    problem = ProblemSerializer()
    observation = ObservationSerializer()
    a1c_todos = TodoSerializer(many=True, read_only=True)
    a1c_notes = AOneCTextNoteSerializer(many=True, read_only=True)

    class Meta:
        model = AOneC
        fields = (
            'id',
            'problem',
            'observation',
            'todo_past_six_months',
            'patient_refused_A1C',
            'a1c_todos',
            'a1c_notes',
            )