from rest_framework import serializers

from emr.models import Observation, AOneCTextNote, ObservationComponent, ObservationComponentTextNote, AOneC

from users_app.serializers import SafeUserSerializer, UserProfileSerializer
from todo_app.serializers import TodoSerializer
from problems_app.serializers import ProblemSerializer
from data_app.serializers import ObservationSerializer


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