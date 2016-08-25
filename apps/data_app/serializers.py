from rest_framework import serializers

from emr.models import Observation, ObservationComponent, ObservationComponentTextNote

from users_app.serializers import SafeUserSerializer, UserProfileSerializer

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
            'name',
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