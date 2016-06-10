from rest_framework import serializers

from emr.models import Encounter, EncounterEvent
from emr.models import EncounterProblemRecord
from problems_app.serializers import ProblemSerializer


class EncounterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Encounter

        fields = (
            'id',
            'physician',
            'patient',
            'starttime',
            'stoptime',
            'audio',
            'video',
            'note',
            'duration',
            'is_active')


class EncounterEventSerializer(serializers.ModelSerializer):

    class Meta:
        model = EncounterEvent

        fields = (
            'id',
            'encounter',
            'datetime',
            'summary',
            'video_seconds',
            'video_timestamp',
            'is_favorite',
            'name_favorite', )
