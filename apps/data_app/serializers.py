from rest_framework import serializers

from emr.models import Observation, ObservationComponent, ObservationValueTextNote, ObservationPinToProblem, \
    ObservationUnit, ObservationValue
from users_app.serializers import UserProfileSerializer, SafeUserSerializer


class ObservationValueTextNoteSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = ObservationValueTextNote
        fields = (
            'id',
            'author',
            'note',
            'datetime',
        )


class ObservationUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservationUnit
        fields = (
            'id',
            'observation',
            'value_unit',
            'is_used',
        )


class ObservationValueSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    observation = serializers.SerializerMethodField()
    value_quantity = serializers.SerializerMethodField()
    observation_value_notes = ObservationValueTextNoteSerializer(many=True, read_only=True)

    class Meta:
        model = ObservationValue
        fields = (
            'id',
            'component',
            'author',
            'value_quantity',
            'effective_datetime',
            'created_on',
            'date',
            'time',
            'observation',
            'observation_value_notes',
        )

    def get_date(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%m/%d/%Y')

    def get_time(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%H:%M')

    def get_observation(self, obj):
        return obj.component.observation.id

    def get_value_quantity(self, obj):
        if obj.value_quantity is not None:
            return "%g" % float(obj.value_quantity)
        else:
            return 0


class ObservationComponentSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    time = serializers.SerializerMethodField()
    author = SafeUserSerializer()
    observation_component_values = ObservationValueSerializer(many=True, read_only=True)

    class Meta:
        model = ObservationComponent
        fields = (
            'id',
            'name',
            'value_quantity',
            'effective_datetime',
            'created_on',
            'author',
            'observation',
            'date',
            'time',
            'observation_component_values',
            'component_code',
        )

    def get_date(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%m/%d/%Y')

    def get_time(self, obj):
        if not obj.effective_datetime:
            return ''
        return obj.effective_datetime.strftime('%H:%M')


class ObservationSerializer(serializers.ModelSerializer):
    subject = SafeUserSerializer()
    encounter = SafeUserSerializer()
    performer = SafeUserSerializer()
    author = SafeUserSerializer()
    observation_components = ObservationComponentSerializer(many=True, read_only=True)
    observation_units = ObservationUnitSerializer(many=True, read_only=True)

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
            'observation_units',
            'color',
            'graph',
        )


class ObservationPinToProblemSerializer(serializers.ModelSerializer):
    author = UserProfileSerializer()

    class Meta:
        model = ObservationPinToProblem
        fields = (
            'id',
            'author',
            'observation',
            'problem',
        )
